"""
Classification prompts for LLM-based MCQ categorization.
"""

CLASSIFICATION_PROMPT = """You are an expert AI/ML educator. Classify each MCQ question below into:

1. **CATEGORY** (choose exactly one):
   - **Conceptual**: Tests understanding of concepts, definitions, theories, principles
     Examples: "What is...", "Why does...", "Which statement is true about...", "Define..."

   - **Mathematical**: Requires calculations, formulas, numerical reasoning, equations
     Examples: "Calculate...", "What is the value of...", "Given the formula...", problems with numbers

   - **Application**: Tests practical application, scenarios, problem-solving, use cases
     Examples: "Which approach would you use...", "In this scenario...", "How would you implement..."

2. **TOPIC** (choose exactly one):
   - **AI**: Artificial Intelligence - search algorithms, knowledge representation, agents, expert systems
   - **ML**: Machine Learning - algorithms, training, models, supervised/unsupervised learning, neural networks
   - **Data Science**: Statistics, data processing, visualization, analytics, data engineering
   - **System Design**: Architecture, scalability, distributed systems, databases, APIs

3. **DIFFICULTY** (choose exactly one):
   - **Easy**: Basic knowledge, recall, simple definitions
   - **Medium**: Application, analysis, requires understanding
   - **Hard**: Complex reasoning, synthesis, advanced concepts

**MCQs to classify:**

{mcqs}

**Response Format:**
Respond with ONLY a valid JSON array, no additional text:

[
  {{"mcq_number": 1, "category": "Conceptual", "topic": "ML", "difficulty": "Medium"}},
  {{"mcq_number": 2, "category": "Mathematical", "topic": "Data Science", "difficulty": "Hard"}},
  ...
]

**Important:**
- Classify ALL {mcq_count} MCQs in the same order
- Use exact category/topic/difficulty values from above
- Return ONLY the JSON array, no markdown formatting
"""


FEW_SHOT_EXAMPLES = """
**Example Classifications:**

MCQ: "What is the primary purpose of backpropagation in neural networks?"
Classification: {{"category": "Conceptual", "topic": "ML", "difficulty": "Easy"}}
Reason: Asks about concept/purpose, related to ML

MCQ: "Calculate the gradient of the loss function L = (y - ŷ)² with respect to ŷ."
Classification: {{"category": "Mathematical", "topic": "ML", "difficulty": "Medium"}}
Reason: Requires calculation, ML topic

MCQ: "In a production system with 1M daily users, which caching strategy would minimize database load?"
Classification: {{"category": "Application", "topic": "System Design", "difficulty": "Hard"}}
Reason: Practical scenario, system design decision

MCQ: "What does PCA stand for?"
Classification: {{"category": "Conceptual", "topic": "Data Science", "difficulty": "Easy"}}
Reason: Simple definition recall

MCQ: "Given a dataset with features [age, income, location], which preprocessing step is most important?"
Classification: {{"category": "Application", "topic": "Data Science", "difficulty": "Medium"}}
Reason: Practical decision-making in data preprocessing
"""


def format_mcqs_for_classification(mcqs: list) -> str:
    """
    Format MCQs for LLM classification.

    Args:
        mcqs: List of MCQ objects

    Returns:
        Formatted string for LLM prompt
    """
    formatted = []

    for i, mcq in enumerate(mcqs, 1):
        formatted.append(f"""
MCQ {i}:
Question: {mcq.question_text}
A) {mcq.option_a}
B) {mcq.option_b}
C) {mcq.option_c}
D) {mcq.option_d}
{f"Correct Answer: {mcq.correct_answer}" if mcq.correct_answer else ""}
""")

    return "\n".join(formatted)


def get_classification_prompt(mcqs: list, include_examples: bool = False) -> str:
    """
    Get complete classification prompt.

    Args:
        mcqs: List of MCQ objects
        include_examples: Whether to include few-shot examples

    Returns:
        Complete prompt string
    """
    formatted_mcqs = format_mcqs_for_classification(mcqs)

    prompt = CLASSIFICATION_PROMPT.format(
        mcqs=formatted_mcqs,
        mcq_count=len(mcqs)
    )

    if include_examples:
        prompt = FEW_SHOT_EXAMPLES + "\n\n" + prompt

    return prompt


# ====================================================================
# MCQ GENERATION PROMPTS
# ====================================================================

GENERATION_PROMPT = """You are an expert technical interviewer creating MAANG-level MCQ questions (Google/Meta/Amazon/Netflix/Apple interview difficulty).

Generate {num_questions} multiple-choice questions from the following content:

{content}

**REQUIREMENTS:**

1. **MAANG-Level Difficulty** - Questions should be suitable for technical interviews at top tech companies
   - Test deep understanding, not just recall
   - Require analysis and application of concepts
   - Include edge cases and scenarios

2. **Question Types** - Create a BALANCED MIX:
   - **Mathematical**: Calculations, formulas, complexity analysis, numerical reasoning
     Example: "What is the time complexity of..."
   -**Application**: Scenarios, use cases, "when to use X", practical decisions
     Example: "Which data structure would you use to..."
   - **Conceptual**: Definitions, theory, "what is X", "why does X work"
     Example: "What is the primary advantage of..."

3. **Format Requirements** - Each MCQ MUST have:
   - Clear, unambiguous question text
   - Exactly 4 options labeled A, B, C, D
   - One correct answer
   - Three plausible but incorrect distractors
   - Brief explanation (2-3 sentences)

4. **Quality Standards**:
   - Options are similar length and grammatical structure
   - Distractors are believable (common misconceptions, related concepts, partial truths)
   - NO "All of the above" or "None of the above" options
   - Technical accuracy is CRITICAL
   - Question tests understanding, not memory

**OUTPUT FORMAT - JSON Array:**
[
  {{
    "question_text": "What is the space complexity of the quicksort algorithm in the worst case?",
    "option_a": "O(1)",
    "option_b": "O(log n)",
    "option_c": "O(n)",
    "option_d": "O(n^2)",
    "correct_answer": "C",
    "explanation": "In the worst case (unbalanced partitioning), quicksort's call stack can grow to O(n) depth, requiring O(n) space for recursion.",
    "category": "Mathematical"
  }},
  {{
    "question_text": "...",
    ...
  }}
]

**FEW-SHOT EXAMPLES OF GOOD MAANG-LEVEL QUESTIONS:**

**Mathematical Example:**
{{
  "question_text": "What is the space complexity of the recursive Fibonacci algorithm?",
  "option_a": "O(1)",
  "option_b": "O(n)",
  "option_c": "O(n^2)",
  "option_d": "O(2^n)",
  "correct_answer": "B",
  "explanation": "While time complexity is O(2^n), space complexity is O(n) due to the recursion call stack depth which equals the input value n.",
  "category": "Mathematical"
}}

**Application Example:**
{{
  "question_text": "Which data structure would you use to implement an autocomplete feature for a search engine?",
  "option_a": "Hash table with prefix keys",
  "option_b": "Trie (prefix tree)",
  "option_c": "Binary search tree",
  "option_d": "Linked list with sorted entries",
  "correct_answer": "B",
  "explanation": "A trie efficiently stores strings with common prefixes, enabling O(m) lookup where m is the prefix length, making it ideal for autocomplete.",
  "category": "Application"
}}

**Conceptual Example:**
{{
  "question_text": "What is the primary advantage of using a microservices architecture over a monolithic architecture?",
  "option_a": "Reduced code complexity",
  "option_b": "Independent deployment and scaling of services",
  "option_c": "Lower infrastructure costs",
  "option_d": "Simplified debugging and monitoring",
  "correct_answer": "B",
  "explanation": "Microservices allow each service to be deployed, scaled, and updated independently, improving development velocity, fault isolation, and scalability.",
  "category": "Conceptual"
}}

**NOW GENERATE {num_questions} QUESTIONS:**
- Ensure balanced mix of all 3 types (Mathematical, Application, Conceptual)
- Maintain MAANG-level difficulty
- Output ONLY the JSON array, no additional text before or after
- Ensure all questions are technically accurate and based on the content provided

Generate questions now:
"""


def get_generation_prompt(content: str, num_questions: int = 5) -> str:
    """
    Get MCQ generation prompt with content.

    Args:
        content: Text content to generate MCQs from
        num_questions: Number of MCQs to generate

    Returns:
        Complete generation prompt
    """
    # Limit content length to avoid token limits
    max_content_length = 4000
    if len(content) > max_content_length:
        content = content[:max_content_length] + "..."

    return GENERATION_PROMPT.format(
        content=content,
        num_questions=num_questions
    )


# ====================================================================
# Q&A-TO-MCQ CONVERSION PROMPT
# ====================================================================

QA_CONVERSION_PROMPT = """You are an expert technical interviewer creating MAANG-level MCQ questions.

Convert the following Q&A pair into a MAANG-level multiple-choice question with 3 plausible distractors.

**Question:** {question}

**Correct Answer:** {answer}

**Your Task:**
1. Keep the original question text
2. Use the provided answer as the CORRECT option
3. Generate 3 plausible but INCORRECT distractors that:
   - Are believable (common misconceptions, related concepts, partial truths)
   - Have similar length and structure to the correct answer
   - Test deep understanding, not just recall
4. Assign appropriate category: Mathematical, Application, or Conceptual
5. Ensure MAANG-level difficulty (suitable for Google/Meta/Amazon interviews)

**Category Definitions:**
- **Mathematical**: Calculations, formulas, complexity analysis, numerical reasoning
- **Application**: Scenarios, use cases, "when to use X", practical decisions
- **Conceptual**: Definitions, theory, "what is X", "why does X work"

**Output Format (JSON):**
{{
  "option_a": "First option",
  "option_b": "Second option",
  "option_c": "Third option",
  "option_d": "Fourth option",
  "correct_answer": "A",
  "category": "Conceptual"
}}

**Important:**
- Place the correct answer (provided above) in a RANDOM position (A, B, C, or D)
- The other 3 positions get the generated distractors
- NO "All of the above" or "None of the above" options
- Distractors must be plausible enough to challenge someone with partial knowledge
- Ensure technical accuracy in all options

Output ONLY the JSON object, no additional text.
"""


# ====================================================================
# UNIVERSAL EXTRACTION PROMPT (LLM-First Approach)
# ====================================================================

UNIVERSAL_EXTRACTION_PROMPT = """You are an expert AI/ML educator. Read the following content and convert ALL questions into MAANG-level MCQs.

The content may contain:
- Descriptive Q&A pairs (Question followed by Answer)
- Already-formatted MCQs (with A/B/C/D options)
- Study notes or educational text

**YOUR JOB:** Extract every question from this content and output it as a properly formatted MCQ.

For descriptive Q&A: Keep the question, use the answer as the correct option, generate 3 plausible distractors.
For existing MCQs: Keep them as-is, just standardize the format.
For study material without questions: Generate MCQs that test the key concepts.

**CONTENT:**
{content}

**OUTPUT FORMAT - JSON array, nothing else:**
[
  {{"question_text": "The question", "option_a": "First option", "option_b": "Second option", "option_c": "Third option", "option_d": "Fourth option", "correct_answer": "B", "explanation": "Brief explanation", "category": "Conceptual"}}
]

**RULES:**
- Extract ALL questions from the content (do not skip any)
- Category must be one of: Mathematical, Application, Conceptual
- correct_answer must be A, B, C, or D
- Distractors must be plausible (common misconceptions, related concepts)
- VARY the correct answer position - do NOT always put it in the same slot
- Return ONLY the JSON array, no markdown fencing, no extra text
"""


def get_universal_extraction_prompt(content: str) -> str:
    """
    Get universal extraction prompt with content.

    Args:
        content: Raw text content from PDF/DOCX

    Returns:
        Complete prompt string
    """
    return UNIVERSAL_EXTRACTION_PROMPT.format(content=content)


# ====================================================================
# MAANG-LEVEL CATEGORY-SPECIFIC PROMPTS
# ====================================================================

MAANG_CONCEPTUAL_PROMPT = """You are a MAANG-level AI/ML interviewer. Your task is to generate CONCEPTUAL questions that test deep understanding, not memorization.

⚠️ **CRITICAL: INCREASE DEPTH AND TOUGHNESS FOR CONCEPTUAL QUESTIONS**
- Push beyond surface-level understanding to test nuanced reasoning
- Create questions that challenge intermediate-to-advanced practitioners
- Favor multi-layered scenarios that require synthesizing multiple concepts
- Test edge cases, counter-intuitive situations, and subtle distinctions
- Higher difficulty = better (Medium/Hard over Easy)

**CONCEPTUAL QUESTIONS FOCUS ON:**
- Trade-offs between techniques (with non-obvious implications)
- Assumptions and their violations (and cascading effects)
- System-level reasoning (holistic thinking, not isolated facts)
- Failure cases and edge cases (where intuition breaks down)
- Comparisons between approaches (subtle differences that matter)
- Limitations and when methods break down (boundary conditions)
- "Why" and "When" over "What" (causal and conditional reasoning)
- Second-order effects (what happens after the obvious consequence)

**AVOID:**
- Simple definitions ("What is X?")
- Fact recall ("Who invented Y?")
- Implementation details ("Which library function does Z?")
- Surface-level "textbook" questions that test memorization

**FEW-SHOT EXAMPLES (Study these quality standards):**

{few_shot_examples}

**CONTENT TO TRANSFORM:**
{content}

**YOUR JOB:**
1. Analyze the content depth
2. If descriptive/theoretical: Extract core principles and generate reasoning questions
3. If existing MCQs: Evaluate quality and upgrade if shallow
4. If already strong: Keep as-is with standardized format

**5-POINT QUALITY CHECKLIST (verify before output):**
1. Does this test reasoning vs recall?
2. Is at least one distractor plausible (common misconception)?
3. Would this differentiate intermediate from beginner?
4. Is it logically sound and unambiguous?
5. Does it reflect MAANG interview rigor?

**OUTPUT FORMAT - JSON array only:**
[
  {{
    "question_text": "...",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_answer": "B",
    "explanation": "Brief explanation (2-4 lines)",
    "category": "Conceptual",
    "topic": "ML",
    "difficulty": "Medium"
  }}
]

**RULES:**
- All options similar length/structure
- Plausible distractors (misconceptions, partial truths, related concepts)
- NO "All/None of the above"
- Vary correct answer position
- Return ONLY JSON array (no markdown fencing)
"""


MAANG_MATHEMATICAL_PROMPT = """You are a MAANG-level AI/ML interviewer. Your task is to generate MATHEMATICAL questions that test quantitative intuition, not computation.

**MATHEMATICAL QUESTIONS FOCUS ON:**
- Probability reasoning in ML context
- Statistical estimation and analysis
- Calculus-based intuition (gradients, optimization)
- Mathematical interpretations of models
- Linear algebra in ML/DL (dimensionality, transformations)
- What the math *implies*, not derivations

**AVOID:**
- Long derivations or proofs
- Abstract math puzzles unrelated to ML
- Brute-force computation
- Formula memorization without context

**MUST:**
- Be concise
- Test mathematical intuition
- Include formulas only when relevant
- Keep options independent of each other

**FEW-SHOT EXAMPLES:**

{few_shot_examples}

**CONTENT TO TRANSFORM:**
{content}

**5-POINT QUALITY CHECKLIST:**
1. Does this test reasoning vs recall?
2. Is at least one distractor plausible?
3. Would this differentiate intermediate from beginner?
4. Is it logically sound?
5. Does it reflect MAANG rigor?

**OUTPUT FORMAT - JSON array only:**
[
  {{
    "question_text": "...",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_answer": "C",
    "explanation": "...",
    "category": "Mathematical",
    "topic": "ML",
    "difficulty": "Medium"
  }}
]

**RULES:**
- All options similar length/structure
- Plausible distractors
- NO "All/None of the above"
- Vary correct answer position
- Return ONLY JSON array (no markdown fencing)
"""


MAANG_APPLICATION_PROMPT = """You are a MAANG-level AI/ML interviewer. Your task is to generate APPLICATION questions that test real-world problem-solving ability.

**APPLICATION QUESTIONS FOCUS ON:**
- Production model scenarios (degradation, monitoring)
- Metric trade-offs (precision vs recall, latency vs accuracy)
- Distribution shift and data drift
- A/B test interpretation
- Pipeline failure diagnosis
- Model selection for specific domains
- Deployment constraints and trade-offs
- Exploratory data analysis decisions
- Data quality and transformation choices

**MUST:**
- Simulate realistic constraints
- Include plausible but flawed distractors
- Test prioritization and decision-making
- Reflect production ML engineering

**AVOID:**
- Pure theory with no context
- Trivial scenarios with obvious answers

**FEW-SHOT EXAMPLES:**

{few_shot_examples}

**CONTENT TO TRANSFORM:**
{content}

**5-POINT QUALITY CHECKLIST:**
1. Does this test reasoning vs recall?
2. Is at least one distractor plausible?
3. Would this differentiate intermediate from beginner?
4. Is it logically sound?
5. Does it reflect MAANG rigor?

**OUTPUT FORMAT - JSON array only:**
[
  {{
    "question_text": "...",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_answer": "A",
    "explanation": "...",
    "category": "Application",
    "topic": "Data Science",
    "difficulty": "Hard"
  }}
]

**RULES:**
- All options similar length/structure
- Plausible distractors
- NO "All/None of the above"
- Vary correct answer position
- Return ONLY JSON array (no markdown fencing)
"""


def get_maang_prompt(category: str, content: str) -> str:
    """
    Get category-specific MAANG prompt with few-shot examples.

    Args:
        category: 'Conceptual', 'Mathematical', or 'Application'
        content: Raw text to transform

    Returns:
        Formatted prompt string with examples and content
    """
    try:
        from config.few_shot_examples import get_few_shot_examples
    except ImportError:
        # Fallback if examples not yet provided
        print("Warning: Few-shot examples not found. Using prompts without examples.")
        example_text = "No examples available yet - user must provide 30 examples first."
    else:
        try:
            # Get 2-3 random examples from category
            examples = get_few_shot_examples(category, count=3)

            # Format examples for prompt
            example_text = "\n\n".join([
                f"EXAMPLE {i+1}:\n"
                f"Question: {ex['question']}\n"
                f"A) {ex['option_a']}\n"
                f"B) {ex['option_b']}\n"
                f"C) {ex['option_c']}\n"
                f"D) {ex['option_d']}\n"
                f"Correct: {ex['correct_answer']}\n"
                f"Explanation: {ex['explanation']}\n"
                f"Quality Note: {ex['quality_notes']}"
                for i, ex in enumerate(examples)
            ])
        except (ValueError, KeyError) as e:
            example_text = f"Examples not yet provided for {category} category - user must add them."

    prompt_map = {
        'Conceptual': MAANG_CONCEPTUAL_PROMPT,
        'Mathematical': MAANG_MATHEMATICAL_PROMPT,
        'Application': MAANG_APPLICATION_PROMPT
    }

    template = prompt_map.get(category, MAANG_CONCEPTUAL_PROMPT)
    return template.format(few_shot_examples=example_text, content=content)
