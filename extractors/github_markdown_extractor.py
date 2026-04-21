"""
GitHub Markdown extractor.

Generic Q&A parser for GitHub-hosted Markdown sources (raw.githubusercontent.com
or github.com repo/blob URLs). Attempts to extract Q&A pairs using forgiving
heading regexes; if the parse is low-confidence (too few pairs or mostly empty
answers) it falls back to the existing ContentGenerator prose path so the caller
still gets MCQs.

The extractor:
  1. Resolves the input URL to a list of raw .md URLs
     - raw.githubusercontent.com/... → single raw URL as-is
     - github.com/user/repo/blob/branch/file.md → raw equivalent
     - github.com/user/repo → list all top-level .md files via GitHub API
  2. Downloads each raw .md file
  3. Tries three question-heading regexes in order (Q\d+, numbered, markdown heading)
  4. For pairs that parse cleanly, calls QAConverter.convert_batch
  5. For files where the parse fails the confidence gate, falls back to
     ContentGenerator.generate_from_content on the raw text

Reused components:
  - generators.qa_converter.QAConverter
  - generators.content_generator.ContentGenerator
  - extractors.base_extractor.BaseExtractor
"""

from typing import List, Optional, Tuple
from urllib.parse import urlparse
import re

try:
    import aiohttp
except ImportError:
    aiohttp = None

from extractors.base_extractor import BaseExtractor
from config.schemas import MCQ


# Confidence gate: at least this many parsed pairs AND at least this fraction
# must have non-trivial answers, otherwise fall through to prose generation.
MIN_PAIRS_FOR_QA = 3
MIN_ANSWER_CHARS = 20
MIN_GOOD_ANSWER_RATIO = 0.5

# Three forgiving heading regexes, tried in order. Each captures a question
# string. Answer is whatever text follows until the next heading match.
_Q_REGEXES = [
    # "Q1:", "Q1.", "Q 12 -" etc.
    re.compile(r"(?im)^\s*Q\s*(\d+)\s*[:.\-\)]\s*(.+?)\s*$"),
    # "1. What is ...?" (numbered list with question mark)
    re.compile(r"(?m)^\s*(\d{1,3})\.\s+(.+\?)\s*$"),
    # "### What is ...?" or "#### How do you ...?"
    re.compile(r"(?m)^\s{0,3}#{2,4}\s+(.+?)\s*$"),
]


class GitHubMarkdownExtractor(BaseExtractor):
    """Extract MCQs from GitHub-hosted Markdown Q&A repositories."""

    def __init__(self, config: dict, media_handler=None, llm_client=None):
        super().__init__(config, media_handler, llm_client)
        self._session: Optional["aiohttp.ClientSession"] = None

    async def extract(self, source: str) -> List[MCQ]:
        if aiohttp is None:
            self.log(
                "aiohttp required for GitHubMarkdownExtractor. Install with: pip install aiohttp",
                "error",
            )
            return []

        self.log(f"GitHub extractor processing: {source}")

        try:
            raw_urls = await self._resolve_to_raw_urls(source)
        except Exception as e:
            self.log(f"Failed to resolve GitHub source {source}: {e}", "error")
            return []

        if not raw_urls:
            self.log(f"No .md files found under {source}", "warning")
            return []

        self.log(f"Found {len(raw_urls)} markdown file(s) to process")

        # Initialize the two downstream paths lazily (both need llm_client)
        qa_converter = None
        content_generator = None
        if self.llm_client is not None:
            from generators.qa_converter import QAConverter
            from generators.content_generator import ContentGenerator

            qa_converter = QAConverter(
                self.llm_client, self.config, strict_validation=False
            )
            content_generator = ContentGenerator(self.llm_client, self.config)
        else:
            self.log(
                "No LLM client attached — cannot convert Q&A or generate from prose",
                "warning",
            )
            return []

        max_conversions = self.config.get("github_max_conversions_per_file", 50)
        all_mcqs: List[MCQ] = []

        for raw_url in raw_urls:
            try:
                text = await self._fetch_raw(raw_url)
            except Exception as e:
                self.log(f"Fetch failed for {raw_url}: {e}", "warning")
                continue

            if not text or len(text.strip()) < 100:
                self.log(f"Skipping near-empty file: {raw_url}", "info")
                continue

            qa_pairs = self._parse_qa_pairs(text)
            pair_count, good_ratio = self._score_pairs(qa_pairs)

            if (
                pair_count >= MIN_PAIRS_FOR_QA
                and good_ratio >= MIN_GOOD_ANSWER_RATIO
            ):
                self.log(
                    f"{raw_url}: parsed {pair_count} Q&A pairs "
                    f"(good-answer ratio {good_ratio:.0%}) → Q&A converter"
                )
                mcqs = await qa_converter.convert_batch(
                    qa_pairs, source=raw_url, max_conversions=max_conversions
                )
                all_mcqs.extend(mcqs)
            else:
                self.log(
                    f"{raw_url}: generic parse weak "
                    f"(pairs={pair_count}, good={good_ratio:.0%}) → prose generator",
                    "info",
                )
                num_q = self.config.get("generation_num_questions", 5)
                min_words = self.config.get("generation_min_content_length", 500)
                if len(text.split()) < min_words:
                    self.log(
                        f"{raw_url}: too short for prose generation "
                        f"({len(text.split())} words < {min_words})",
                        "warning",
                    )
                    continue
                mcqs = await content_generator.generate_from_content(
                    text, raw_url, num_questions=num_q
                )
                all_mcqs.extend(mcqs)

        await self._close_session()
        self.log(f"GitHub extractor produced {len(all_mcqs)} MCQs from {source}")
        return all_mcqs

    # ------------------------------------------------------------------ URL resolution

    async def _resolve_to_raw_urls(self, source: str) -> List[str]:
        """Map an arbitrary GitHub URL to a list of raw markdown URLs."""
        parsed = urlparse(source)
        host = (parsed.netloc or "").lower()
        path_parts = [p for p in parsed.path.split("/") if p]

        # Already a raw URL → use directly if it looks like markdown
        if host == "raw.githubusercontent.com":
            if source.lower().endswith((".md", ".markdown")):
                return [source]
            # Try .md anyway — some raw URLs omit extension; best-effort
            return [source]

        if host not in ("github.com", "www.github.com"):
            raise ValueError(f"Not a GitHub URL: {source}")

        if len(path_parts) < 2:
            raise ValueError(f"GitHub URL missing user/repo: {source}")

        user, repo = path_parts[0], path_parts[1]

        # /user/repo/blob/branch/path/to/file.md
        if len(path_parts) >= 5 and path_parts[2] == "blob":
            branch = path_parts[3]
            file_path = "/".join(path_parts[4:])
            if file_path.lower().endswith((".md", ".markdown")):
                return [
                    f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{file_path}"
                ]
            raise ValueError(f"Blob URL is not a markdown file: {source}")

        # /user/repo/tree/branch/dir → list that subdirectory
        if len(path_parts) >= 5 and path_parts[2] == "tree":
            branch = path_parts[3]
            sub_path = "/".join(path_parts[4:])
            return await self._list_markdown_via_api(user, repo, sub_path, branch)

        # /user/repo → list repo root .md files on default branch
        return await self._list_markdown_via_api(user, repo, "", None)

    async def _list_markdown_via_api(
        self, user: str, repo: str, sub_path: str, branch: Optional[str]
    ) -> List[str]:
        """Use GitHub Contents API to enumerate .md files in a directory."""
        api_url = f"https://api.github.com/repos/{user}/{repo}/contents/{sub_path}"
        if branch:
            api_url = f"{api_url}?ref={branch}"

        headers = {"Accept": "application/vnd.github+json"}
        timeout_s = self.config.get("request_timeout", 30)

        session = await self._get_session()
        async with session.get(api_url, headers=headers, timeout=timeout_s) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise RuntimeError(
                    f"GitHub API {resp.status} for {api_url}: {body[:200]}"
                )
            data = await resp.json()

        if not isinstance(data, list):
            return []

        raw_urls = []
        for entry in data:
            if entry.get("type") != "file":
                continue
            name = entry.get("name", "").lower()
            if not name.endswith((".md", ".markdown")):
                continue
            # Skip license/contributing/code-of-conduct type files
            if name in {"license.md", "contributing.md", "code_of_conduct.md"}:
                continue
            download = entry.get("download_url")
            if download:
                raw_urls.append(download)

        return raw_urls

    # ------------------------------------------------------------------ Fetch

    async def _get_session(self) -> "aiohttp.ClientSession":
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _close_session(self):
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

    async def _fetch_raw(self, url: str) -> str:
        timeout_s = self.config.get("request_timeout", 30)
        session = await self._get_session()
        async with session.get(url, timeout=timeout_s) as resp:
            resp.raise_for_status()
            return await resp.text()

    # ------------------------------------------------------------------ Q&A parsing

    def _parse_qa_pairs(self, text: str) -> List[dict]:
        """Try each heading regex in order; return pairs from the best-yielding one."""
        best: List[dict] = []
        for regex in _Q_REGEXES:
            pairs = self._extract_with_regex(text, regex)
            if len(pairs) > len(best):
                best = pairs
            # Early exit if we have a strong result
            if len(best) >= 5:
                return best
        return best

    def _extract_with_regex(self, text: str, regex: "re.Pattern") -> List[dict]:
        """Extract Q&A pairs where answer = text between this match and the next."""
        matches = list(regex.finditer(text))
        if not matches:
            return []

        pairs: List[dict] = []
        for i, m in enumerate(matches):
            # Question text is the last capture group (handles both 1- and 2-group patterns)
            question = m.group(m.lastindex).strip() if m.lastindex else ""
            if not question:
                continue

            # Strip trailing markdown heading markers ("### Q1: foo ###" -> "Q1: foo")
            question = re.sub(r"\s*#{1,6}\s*$", "", question).strip()

            if len(question) < 8:
                continue

            # Drop obvious section headers: no "?", no "Q<n>" prefix, and short.
            # These leak in from markdown TOC sections like "## Questions ##".
            has_q_mark = "?" in question
            has_q_prefix = bool(re.match(r"^\s*Q\s*\d+", question, re.IGNORECASE))
            if not has_q_mark and not has_q_prefix:
                continue

            answer_start = m.end()
            answer_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            answer = text[answer_start:answer_end].strip()

            # Strip leading "A:" / "Answer:" labels
            answer = re.sub(
                r"^(answer|ans|a)\s*[:\-]\s*",
                "",
                answer,
                flags=re.IGNORECASE,
            ).strip()

            pairs.append({"question": question, "answer": answer})

        return pairs

    def _score_pairs(self, pairs: List[dict]) -> Tuple[int, float]:
        if not pairs:
            return 0, 0.0
        good = sum(1 for p in pairs if len(p.get("answer", "")) >= MIN_ANSWER_CHARS)
        return len(pairs), good / len(pairs)
