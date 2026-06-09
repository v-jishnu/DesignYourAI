"""
Post-generation evaluation pipeline for the MCQ knowledge base.

This package is a STANDALONE feature that runs AFTER an Excel KB is produced.
It independently re-judges every MCQ with an LLM (local Ollama now, any
OpenAI-compatible / Gemini / Anthropic API later) to answer four questions:

    1. Are the options sufficient to answer the question at all? (answerability)
    2. Which option does the LLM independently believe is correct? (blind pick)
    3. Does the stored Correct_Answer agree with the blind pick? (answer match)
    4. Does the Explanation justify the marked correct option? (explanation consistency)

It does NOT import from or modify the generation path (extractors, generators,
validators). It only reads the shared, stable contracts: config.schemas.MCQ and
config.settings.Settings.
"""
