"""
Quality validation for MAANG-level MCQ generation.
Implements 5-point quality checklist to ensure interview-grade questions.
"""

import logging
from typing import Tuple, Dict, List
from config.schemas import MCQ


class QualityValidator:
    """Validates MCQ quality against MAANG-level standards."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_mcq(self, mcq: MCQ, strict: bool = True) -> Tuple[bool, str, Dict[str, bool]]:
        """
        5-point quality check for MCQ.

        Args:
            mcq: MCQ object to validate
            strict: If False, relaxes distractors length check, allows Easy
                    difficulty, and is more lenient on industry_rigor. Useful
                    for pre-vetted sources like StrataScratch.

        Returns:
            Tuple of (pass/fail, failure_reason, detailed_checks)
        """
        checks = {
            'reasoning_vs_recall': self._check_reasoning(mcq),
            'plausible_distractors': self._check_distractors(mcq, strict=strict),
            'differentiates_levels': self._check_differentiation(mcq, strict=strict),
            'logically_sound': self._check_logic(mcq),
            'industry_rigor': self._check_rigor(mcq, strict=strict),
            'answer_explanation_consistent': self._check_answer_explanation_consistency(mcq),
        }

        # All checks must pass
        all_passed = all(checks.values())

        if not all_passed:
            failed = [k for k, v in checks.items() if not v]
            reason = f"Failed checks: {', '.join(failed)}"
        else:
            reason = "Passed all quality checks"

        return all_passed, reason, checks

    def _check_reasoning(self, mcq: MCQ) -> bool:
        """
        Check 1: Tests reasoning vs recall.

        Heuristics:
        - Question contains "why", "when", "how", "trade-off", "impact", "scenario"
        - NOT simple "what is", "define", "which of the following"
        - Category is appropriate (Conceptual/Application for reasoning)
        """
        question_lower = mcq.question_text.lower()

        # Positive signals (reasoning keywords)
        reasoning_keywords = ['why', 'when', 'how', 'trade-off', 'impact', 'cause', 'effect',
                             'scenario', 'production', 'fail', 'improve', 'better', 'worse',
                             'most likely', 'root cause', 'best approach', 'violate', 'assume',
                             'limitation', 'drawback', 'advantage', 'disadvantage', 'compare',
                             'contrast', 'prefer', 'choose', 'appropriate', 'suitable']

        # Negative signals (recall keywords)
        recall_keywords = ['what is', 'define', 'which of the following is', 'what does',
                          'who invented', 'in which year', 'what stands for', 'name the',
                          'list the', 'identify the']

        has_reasoning = any(kw in question_lower for kw in reasoning_keywords)
        has_recall = any(kw in question_lower for kw in recall_keywords)

        # Mathematical questions can be recall-style (testing formula understanding)
        if mcq.category == 'Mathematical':
            return True  # More lenient for math questions

        return has_reasoning or not has_recall

    def _check_distractors(self, mcq: MCQ, strict: bool = True) -> bool:
        """
        Check 2: Plausible distractors.

        Heuristics:
        - All options similar length (within 50%/80% of each other depending on strict)
        - No obvious wrong answers ("None of the above", "All of the above")
        - Options grammatically consistent
        """
        options = [mcq.option_a, mcq.option_b, mcq.option_c, mcq.option_d]

        # Check for obvious bad distractors
        bad_patterns = ['none of the above', 'all of the above', 'both a and b',
                       'option a and b', 'i don\'t know', 'invalid', 'not applicable',
                       'cannot be determined']

        for opt in options:
            if any(bad in opt.lower() for bad in bad_patterns):
                return False

        # Check option length similarity
        lengths = [len(opt) for opt in options]
        avg_length = sum(lengths) / len(lengths)

        if avg_length == 0:
            return False

        # Relaxed mode allows more length variation (80% vs 50%)
        threshold = 0.8 if not strict else 0.5
        length_variance = all(abs(l - avg_length) / avg_length < threshold for l in lengths)

        return length_variance

    def _check_differentiation(self, mcq: MCQ, strict: bool = True) -> bool:
        """
        Check 3: Differentiates intermediate from beginner.

        Heuristics:
        - Difficulty marked as Medium or Hard (Easy allowed in relaxed mode)
        - Question length > 20 words (>10 in relaxed mode)
        - Explanation exists (shows depth)
        """
        # MAANG questions should be Medium or Hard; relaxed allows Easy
        if strict and mcq.difficulty not in ['Medium', 'Hard']:
            return False
        if not strict and mcq.difficulty not in ['Easy', 'Medium', 'Hard']:
            return False

        # Complex questions are longer
        word_count = len(mcq.question_text.split())
        min_words = 20 if strict else 10
        if word_count < min_words:
            return False

        # Should have explanation
        if not mcq.explanation or len(mcq.explanation.strip()) < 20:
            return False

        return True

    def _check_logic(self, mcq: MCQ) -> bool:
        """
        Check 4: Logically sound and unambiguous.

        Heuristics:
        - Correct answer is one of A/B/C/D
        - All options are non-empty
        - Question is clear (no multiple questions)
        """
        # Valid answer
        if mcq.correct_answer not in ['A', 'B', 'C', 'D']:
            return False

        # All options filled
        options = [mcq.option_a, mcq.option_b, mcq.option_c, mcq.option_d]
        if any(not opt or len(opt.strip()) < 5 for opt in options):
            return False

        # Question not too convoluted (heuristic: max 3 question marks)
        if mcq.question_text.count('?') > 3:
            return False

        return True

    def _check_rigor(self, mcq: MCQ, strict: bool = True) -> bool:
        """
        Check 5: Reflects MAANG interview standards.

        Heuristics:
        - Category is appropriate (Conceptual, Mathematical, Application)
        - Topic is within scope (AI, ML, Data Science, System Design)
        - No typos or grammar issues (basic check)

        In relaxed mode: auto-corrects category/topic to nearest valid value
        instead of failing outright.
        """
        valid_categories = ['Conceptual', 'Mathematical', 'Application']
        valid_topics = ['AI', 'ML', 'Data Science', 'System Design']

        if strict:
            if mcq.category not in valid_categories:
                return False
            if mcq.topic not in valid_topics:
                return False
        else:
            # Auto-correct category if close enough
            if mcq.category not in valid_categories:
                cat_lower = (mcq.category or '').lower()
                if 'concept' in cat_lower or 'theory' in cat_lower:
                    mcq.category = 'Conceptual'
                elif 'math' in cat_lower or 'quant' in cat_lower:
                    mcq.category = 'Mathematical'
                elif 'app' in cat_lower or 'applied' in cat_lower or 'scenario' in cat_lower:
                    mcq.category = 'Application'
                else:
                    mcq.category = 'Conceptual'  # default

            if mcq.topic not in valid_topics:
                topic_lower = (mcq.topic or '').lower()
                if 'ml' in topic_lower or 'machine' in topic_lower:
                    mcq.topic = 'ML'
                elif 'data' in topic_lower or 'statistic' in topic_lower or 'analy' in topic_lower:
                    mcq.topic = 'Data Science'
                elif 'system' in topic_lower or 'design' in topic_lower or 'architect' in topic_lower:
                    mcq.topic = 'System Design'
                else:
                    mcq.topic = 'AI'  # default

        # Basic grammar check (capitalization, no excessive punctuation)
        if not mcq.question_text[0].isupper():
            return False

        # No excessive punctuation
        if mcq.question_text.count('!') > 2 or mcq.question_text.count('...') > 1:
            return False

        return True

    def _check_answer_explanation_consistency(self, mcq: MCQ) -> bool:
        """
        Check 6: The explanation is consistent with the declared correct answer.

        Heuristic: at least one significant word (>4 chars) from the correct option's
        text should appear in the explanation. This catches the common failure where the
        LLM's explanation describes a different option than the one marked correct —
        which is the primary source of wrong-answer generation after shuffling.

        Returns True if explanation is absent/short (not enough signal to judge).
        """
        if not mcq.explanation or len(mcq.explanation.strip()) < 20:
            return True  # No explanation to cross-check; other checks cover this

        option_map = {'A': mcq.option_a, 'B': mcq.option_b,
                      'C': mcq.option_c, 'D': mcq.option_d}
        correct_option = option_map.get(mcq.correct_answer, '')
        if not correct_option:
            return False

        explanation_lower = mcq.explanation.lower()
        correct_words = [w.lower() for w in correct_option.split() if len(w) > 4]

        if not correct_words:
            return True  # Option too short to extract signal words

        overlap = sum(1 for w in correct_words if w in explanation_lower)
        return overlap >= max(1, len(correct_words) // 3)

    def batch_validate(self, mcqs: List[MCQ]) -> Tuple[List[MCQ], List[Tuple[MCQ, str]], dict]:
        """
        Validate batch of MCQs.

        Args:
            mcqs: List of MCQ objects to validate

        Returns:
            Tuple of (passed_mcqs, failed_mcqs, stats)
        """
        passed = []
        failed = []
        stats = {
            'total': len(mcqs),
            'passed': 0,
            'failed': 0,
            'pass_rate': 0.0,
            'failures_by_check': {
                'reasoning_vs_recall': 0,
                'plausible_distractors': 0,
                'differentiates_levels': 0,
                'logically_sound': 0,
                'industry_rigor': 0,
                'answer_explanation_consistent': 0,
            }
        }

        for mcq in mcqs:
            is_valid, reason, checks = self.validate_mcq(mcq)

            if is_valid:
                passed.append(mcq)
                stats['passed'] += 1
            else:
                failed.append((mcq, reason))
                stats['failed'] += 1

                # Track which checks failed
                for check_name, check_result in checks.items():
                    if not check_result:
                        stats['failures_by_check'][check_name] += 1

        stats['pass_rate'] = stats['passed'] / stats['total'] if stats['total'] > 0 else 0.0

        self.logger.info(f"Quality validation: {stats['passed']}/{stats['total']} passed ({stats['pass_rate']*100:.1f}%)")

        return passed, failed, stats
