"""
Prompts for the LLM judge.

One combined prompt per row: the judge returns answerability + blind answer +
explanation consistency in a single JSON object. This keeps local Ollama runs
fast (one call per MCQ instead of three).

Design constraints:
- The stored Correct_Answer is NEVER shown to the judge when it picks the answer
  (blind pick section). Showing it causes sycophantic rubber-stamping.
- The explanation IS shown for check 4, but only after the blind pick is locked.
- All three checks come back in one structured JSON so parsing is done once.
"""


def get_combined_judge_prompt(
    question_text: str,
    option_a: str,
    option_b: str,
    option_c: str,
    option_d: str,
    explanation: str | None,
    stored_answer: str | None,
) -> str:
    """
    Build the single combined evaluation prompt for one MCQ row.

    The stored_answer is passed in ONLY for check 3 (answer-match comparison),
    which the model does after it has already committed its blind pick. This
    preserves the independence of the blind pick while letting the model
    self-report the match, avoiding a separate comparison step in Python.

    Args:
        question_text: The question stem.
        option_a..d: The four answer options.
        explanation: The explanation stored in the KB (may be None/empty).
        stored_answer: The Correct_Answer letter stored in the KB (may be None).

    Returns:
        Prompt string ready to send to the judge LLM.
    """
    explanation_block = (
        f'"{explanation.strip()}"' if explanation and explanation.strip()
        else "NO EXPLANATION PROVIDED"
    )
    stored_block = stored_answer.strip().upper() if stored_answer else "NOT PROVIDED"

    return f"""You are an expert AI/ML educator acting as an independent MCQ quality evaluator.

You will evaluate the following multiple-choice question across three independent checks.
IMPORTANT: Complete CHECK 1 and CHECK 2 BEFORE reading the stored answer or explanation.

==============================
QUESTION:
{question_text.strip()}

OPTIONS:
A) {option_a.strip()}
B) {option_b.strip()}
C) {option_c.strip()}
D) {option_d.strip()}
==============================

--- CHECK 1: ANSWERABILITY ---
Without looking at the stored answer, judge whether these four options are well-formed
and sufficient to answer the question. Fail if ANY of:
- Fewer than two options are meaningfully distinct
- An option says "All of the above", "None of the above", "Both A and B"
- Two or more options are near-identical in meaning
- No option is defensibly correct based on your knowledge

--- CHECK 2: BLIND ANSWER PICK ---
Ignoring the stored answer entirely, use your domain knowledge to determine which
option (A/B/C/D) is CORRECT. Reason carefully. If you cannot confidently pick one,
still give your best pick and mark confidence low.

--- NOW READ: Stored answer and explanation ---
Stored Correct_Answer: {stored_block}
Explanation: {explanation_block}

--- CHECK 3: ANSWER MATCH ---
Does your blind pick from Check 2 match the stored Correct_Answer?
(If stored answer was NOT PROVIDED, mark as N/A)

--- CHECK 4: EXPLANATION CONSISTENCY ---
Does the explanation above logically justify the STORED correct option (not yours)?
Fail if:
- The explanation's reasoning points at a different option than the stored one
- The explanation contradicts the stored answer
- The explanation is so vague it could justify any option
If NO EXPLANATION PROVIDED, mark as N/A.

==============================
Return ONLY a valid JSON object with NO markdown fencing, exactly this shape:

{{
  "answerable": "PASS" | "FAIL",
  "llm_answer": "A" | "B" | "C" | "D",
  "answer_match": "PASS" | "FAIL" | "N/A",
  "explanation_consistent": "PASS" | "FAIL" | "N/A",
  "confidence": 0.0,
  "rationale": "one sentence summarising the most important finding"
}}

Rules:
- confidence is a float 0.0–1.0 reflecting your certainty in the blind pick
- rationale is one plain-English sentence, no bullet points
- Return ONLY the JSON object — no preamble, no trailing text
"""
