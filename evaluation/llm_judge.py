"""
LLMJudge: thin wrapper around the same dual-path LLM client contract used
throughout the ingestion pipeline (Gemini `.client.models` vs OpenAI-compatible
`.chat.completions`).

Wired to local Ollama (qwen2.5:7b) by default.  Swap to any external API by
changing LLM_PROVIDER in .env — no code change required.

Key differences from the extractor client:
- temperature=0 for deterministic, reproducible judgements
- async-only (the pipeline is fully async with a concurrency semaphore)
- returns raw text; parsing lives in evaluators.py
"""

import asyncio
import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def build_judge_client(config: dict):
    """
    Build an LLM client for the evaluator using the same factory pattern as
    extraction_agent.py.  Returns a client object with `.model_name` attached.

    Supported providers: gemini, openai, groq, together, qwen, deepseek, ollama.
    """
    llm_config = config.get("llm_config", {})
    provider = llm_config.get("provider", "ollama")

    if provider == "gemini":
        from google import genai  # type: ignore
        client = genai.Client(api_key=llm_config["api_key"])
        client.model_name = llm_config["model"]
        client.provider = provider
        return client

    # OpenAI-compatible (ollama, groq, openai, together, qwen, deepseek)
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise ImportError("openai package required: pip install openai")

    base_url = llm_config.get("base_url")
    client = AsyncOpenAI(
        api_key=llm_config.get("api_key", "ollama"),
        base_url=base_url,
    )
    client.model_name = llm_config["model"]
    client.provider = provider
    return client


class LLMJudge:
    """Calls the LLM judge and returns the raw response text."""

    def __init__(self, client, max_retries: int = 3):
        self.client = client
        self.max_retries = max_retries

    async def judge(self, prompt: str) -> Optional[str]:
        """
        Send a prompt to the judge LLM.  Returns raw response text or None.
        Retries on 429 rate-limit with exponential backoff.
        """
        for attempt in range(self.max_retries):
            try:
                # Gemini path
                if (
                    hasattr(self.client, "client")
                    and hasattr(self.client.client, "models")
                ):
                    response = self.client.client.models.generate_content(
                        model=self.client.model_name,
                        contents=prompt,
                    )
                    return response.text

                # OpenAI-compatible path (Ollama, Groq, OpenAI, …)
                response = await self.client.chat.completions.create(
                    model=self.client.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                return response.choices[0].message.content

            except Exception as exc:
                err = str(exc)
                if ("429" in err or "rate" in err.lower()) and attempt < self.max_retries - 1:
                    wait = min(30 * (attempt + 1), 90)
                    logger.warning(f"Rate limited, waiting {wait}s (attempt {attempt+1}/{self.max_retries})")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"LLM judge call failed (attempt {attempt+1}): {exc}")
                    if attempt == self.max_retries - 1:
                        return None
                    await asyncio.sleep(3)

        return None

    def parse_response(self, raw: str) -> Optional[dict]:
        """
        Parse the judge's JSON response robustly.

        Handles:
        - Bare JSON object
        - JSON wrapped in ```json ... ``` fences
        - Extra text before/after the object
        """
        if not raw:
            return None

        text = raw.strip()

        # Strip markdown fences
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text.rstrip())
            text = text.strip()

        # Extract first {...} block
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            logger.error(f"No JSON object found in judge response: {raw[:200]}")
            return None

        text = text[start : end + 1]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fix common local-model JSON issues
            text = re.sub(r",\s*\}", "}", text)
            text = re.sub(r",\s*\]", "]", text)
            try:
                return json.loads(text)
            except json.JSONDecodeError as exc:
                logger.error(f"Failed to parse judge JSON: {exc} | text: {text[:300]}")
                return None
