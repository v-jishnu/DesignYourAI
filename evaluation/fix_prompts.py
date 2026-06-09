"""
Prompts for the MCQ fixer.

Each prompt targets a specific failure type and asks the LLM to return
only what needs to change — never the question text or options, which are
treated as immutable source material.
"""


def get_fix_wrong_answer_prompt(
    question_text: str,
    option_a: str,
    option_b: str,
    option_c: str,
    option_d: str,
    correct_letter: str,
) -> str:
    """
    Prompt for WRONG_ANSWER rows.

    The evaluator's blind pick (correct_letter) is passed in as the answer to use.
    The LLM's job is ONLY to write a clear explanation justifying that answer.
    It must not change the question or options.
    """
    return f"""You are an expert AI/ML educator. The following multiple-choice question has been flagged because its stored correct answer was wrong. The correct answer has already been determined to be option {correct_letter}.

QUESTION:
{question_text.strip()}

OPTIONS:
A) {option_a.strip()}
B) {option_b.strip()}
C) {option_c.strip()}
D) {option_d.strip()}

CORRECT ANSWER: {correct_letter}

Your task: Write a clear, accurate explanation (2-4 sentences) that:
1. States why option {correct_letter} is correct using domain knowledge
2. Briefly notes why the other options are incorrect or less accurate
3. Is factually precise — no vague or generic statements

Return ONLY a valid JSON object, no markdown fencing:

{{"correct_answer": "{correct_letter}", "explanation": "..."}}

Rules:
- correct_answer must be exactly "{correct_letter}"
- explanation must specifically reference the content of option {correct_letter}
- Do not change or reference the question text
- Return ONLY the JSON object
"""


def get_fix_bad_explanation_prompt(
    question_text: str,
    option_a: str,
    option_b: str,
    option_c: str,
    option_d: str,
    correct_letter: str,
) -> str:
    """
    Prompt for BAD_EXPLANATION rows.

    The stored correct answer is right; only the explanation needs to be rewritten
    to actually justify that answer instead of describing a different option.
    """
    return f"""You are an expert AI/ML educator. The following multiple-choice question has a correct answer that is right, but its explanation was flagged as inconsistent — it describes a different option instead of justifying the marked correct answer.

QUESTION:
{question_text.strip()}

OPTIONS:
A) {option_a.strip()}
B) {option_b.strip()}
C) {option_c.strip()}
D) {option_d.strip()}

CORRECT ANSWER: {correct_letter}

Your task: Write a replacement explanation (2-4 sentences) that:
1. Clearly justifies why option {correct_letter} is correct
2. Briefly explains why the other options are wrong or less accurate
3. Is specific — mentions key terms from option {correct_letter}'s text

Return ONLY a valid JSON object, no markdown fencing:

{{"correct_answer": "{correct_letter}", "explanation": "..."}}

Rules:
- correct_answer must be exactly "{correct_letter}" (do not change it)
- explanation must be clearly about option {correct_letter}, not any other option
- Return ONLY the JSON object
"""
