"""
StrataScratch extractor for pulling technical interview questions via GraphQL API.

Fetches Q&A pairs (question + detailed solution) from StrataScratch's
Non-Coding Technical Questions and outputs them for the Q&A-to-MCQ pipeline.

Uses sync `requests` library (wrapped with asyncio.to_thread) for Windows compatibility.
"""

import asyncio
import logging
import time
from typing import List, Optional

try:
    import requests as req_lib
except ImportError:
    req_lib = None

from extractors.base_extractor import BaseExtractor
from config.schemas import MCQ


# GraphQL API endpoint
API_URL = "https://api.stratascratch.com/graphql/"

# Query to list all technical questions (paginated)
LIST_QUERY = """
query NonCodingQuestions(
    $first: Int!, $offset: Int!, $q: String,
    $questionTypes: [String], $userSolutionState: String,
    $orderField: String, $companies: [Int], $difficulties: [Int],
    $industries: [Int], $jobPositions: [Int]
) {
    allTechnicalQuestions(
        first: $first, offset: $offset, q: $q,
        questionTypes: $questionTypes, userSolutionState: $userSolutionState,
        orderField: $orderField, companies: $companies, difficulties: $difficulties,
        industries: $industries, jobPositions: $jobPositions
    ) {
        totalCount
        edges {
            node {
                id
                difficulty
                questionType
                companies { id name }
                url
                questionShort
                isFreemium
            }
        }
    }
}
"""

# Query to fetch full question detail by slug
DETAIL_QUERY = """
query TechnicalQuestion($slug: String!) {
    technicalQuestion(slug: $slug) {
        id
        slug
        question
        questionShort
        questionType
        difficulty
        company { id name }
        solution
        isFreemium
        interviewDate
        lastUpdated
        jobPositions { id name }
    }
}
"""

# Difficulty mapping: API returns int, we use string
DIFFICULTY_MAP = {1: "Easy", 2: "Medium", 3: "Hard"}


class StrataScratchExtractor(BaseExtractor):
    """Extract technical interview Q&A pairs from StrataScratch via GraphQL API."""

    def __init__(self, config: dict, media_handler=None, llm_client=None):
        super().__init__(config, media_handler, llm_client)
        self.auth_token = config.get('stratascratch_token')
        self.page_size = config.get('stratascratch_page_size', 50)
        self.request_delay = config.get('stratascratch_request_delay', 0.5)
        # Filters
        self.job_positions = config.get('stratascratch_job_positions', [])
        self.question_types = config.get('stratascratch_question_types', [])
        self.difficulties = config.get('stratascratch_difficulties', [])
        self.companies = config.get('stratascratch_companies', [])
        # Limit how many question details to fetch (0 = all)
        self.max_details = config.get('stratascratch_max_details', 0)

    async def extract(self, source: str) -> List[MCQ]:
        """
        Extract Q&A pairs from StrataScratch and return as MCQ placeholders.

        The returned MCQs have the question in question_text and the solution
        in explanation. Options are placeholders — the Q&A-to-MCQ pipeline
        should be used to convert these into proper MCQs.

        Args:
            source: Identifier string (e.g., "stratascratch" or the platform URL)

        Returns:
            List of MCQ objects with Q&A data
        """
        if req_lib is None:
            self.log("requests library required. Install with: pip install requests", 'error')
            return []

        if not self.auth_token:
            self.log("StrataScratch auth token not configured. Set 'stratascratch_token' in config.", 'error')
            return []

        self.log("Fetching questions from StrataScratch API...")

        try:
            # Run sync HTTP calls in a thread to avoid blocking the event loop
            result = await asyncio.to_thread(self._extract_sync)
            return result
        except Exception as e:
            self.log(f"Error extracting from StrataScratch: {e}", 'error')
            return []

    def _extract_sync(self) -> List[MCQ]:
        """Synchronous extraction logic (runs in thread)."""
        headers = self._build_headers()
        session = req_lib.Session()
        session.headers.update(headers)

        # Step 1: Get all question slugs
        slugs = self._fetch_question_list_sync(session)
        if not slugs:
            self.log("No questions found matching filters", 'warning')
            return []

        # Apply max_details limit if set
        if self.max_details > 0:
            slugs = slugs[:self.max_details]

        self.log(f"Found {len(slugs)} questions, fetching full content...")

        # Step 2: Fetch full details for each question
        mcqs = self._fetch_all_details_sync(session, slugs)
        self.log(f"Fetched {len(mcqs)} complete Q&A pairs")

        session.close()
        return mcqs

    def get_qa_pairs(self, mcqs: List[MCQ]) -> list:
        """
        Convert extracted MCQs back to Q&A pair format for the QAConverter pipeline.

        Args:
            mcqs: List of MCQ objects from extract()

        Returns:
            List of dicts with 'question' and 'answer' keys
        """
        return [
            {'question': mcq.question_text, 'answer': mcq.explanation}
            for mcq in mcqs
            if mcq.explanation
        ]

    def _fetch_question_list_sync(self, session) -> List[dict]:
        """Fetch all question metadata via paginated GraphQL queries."""
        all_questions = []
        offset = 0

        # First request to get total count
        variables = self._build_list_variables(offset)
        data = self._graphql_request_sync(session, LIST_QUERY,
                                           "NonCodingQuestions", variables)
        if not data:
            return []

        result = data.get('allTechnicalQuestions', {})
        total_count = result.get('totalCount', 0)
        edges = result.get('edges', [])
        all_questions.extend(self._extract_slugs_from_edges(edges))

        self.log(f"Total questions available: {total_count}")

        # Fetch remaining pages
        while offset + self.page_size < total_count:
            offset += self.page_size
            time.sleep(self.request_delay)

            variables = self._build_list_variables(offset)
            data = self._graphql_request_sync(session, LIST_QUERY,
                                               "NonCodingQuestions", variables)
            if not data:
                break

            edges = data.get('allTechnicalQuestions', {}).get('edges', [])
            all_questions.extend(self._extract_slugs_from_edges(edges))

            self.log(f"Fetched {len(all_questions)}/{total_count} question metadata...")

        return all_questions

    def _fetch_all_details_sync(self, session, questions: List[dict]) -> List[MCQ]:
        """Fetch full question + solution for each question slug."""
        mcqs = []

        for i, q in enumerate(questions, 1):
            slug = q['slug']
            time.sleep(self.request_delay)

            data = self._graphql_request_sync(
                session, DETAIL_QUERY,
                "TechnicalQuestion", {"slug": slug}
            )

            if not data:
                self.log(f"Failed to fetch detail for {slug}", 'warning')
                continue

            detail = data.get('technicalQuestion')
            if not detail:
                continue

            question_text = detail.get('question', '').strip()
            solution = detail.get('solution', '').strip()

            if not question_text:
                continue

            # Map difficulty
            difficulty_int = detail.get('difficulty', 2)
            difficulty = DIFFICULTY_MAP.get(difficulty_int, 'Medium')

            # Build source URL
            source_url = f"https://platform.stratascratch.com/technical/{slug}"

            # Company name
            company = detail.get('company', {})
            company_name = company.get('name', '') if company else ''

            # Job positions
            positions = detail.get('jobPositions', [])
            position_names = [p.get('name', '') for p in positions] if positions else []

            # Determine topic from questionType
            question_type = detail.get('questionType', '')
            topic = self._map_question_type_to_topic(question_type)

            mcq = MCQ(
                question_text=question_text,
                option_a="[PENDING_CONVERSION]",
                option_b="[PENDING_CONVERSION]",
                option_c="[PENDING_CONVERSION]",
                option_d="[PENDING_CONVERSION]",
                source=source_url,
                explanation=solution if solution else None,
                difficulty=difficulty,
                topic=topic,
                company=company_name if company_name else None,
                job_roles=', '.join(position_names) if position_names else None,
            )

            mcqs.append(mcq)

            if i % 25 == 0:
                self.log(f"Fetched {i}/{len(questions)} question details...")

        return mcqs

    def _graphql_request_sync(self, session, query: str,
                               operation_name: str, variables: dict) -> Optional[dict]:
        """Execute a GraphQL request with error handling."""
        payload = {
            "operationName": operation_name,
            "query": query,
            "variables": variables
        }

        try:
            resp = session.post(API_URL, json=payload, timeout=30)

            if resp.status_code == 429:
                self.log("Rate limited by StrataScratch API, waiting 30s...", 'warning')
                time.sleep(30)
                # Retry once
                resp = session.post(API_URL, json=payload, timeout=30)
                if resp.status_code != 200:
                    self.log(f"API request failed after retry: {resp.status_code}", 'error')
                    return None

            if resp.status_code != 200:
                self.log(f"API request failed: {resp.status_code}", 'error')
                return None

            result = resp.json()

            if 'errors' in result:
                self.log(f"GraphQL errors: {result['errors']}", 'error')
                return None

            return result.get('data')

        except Exception as e:
            self.log(f"GraphQL request error: {e}", 'error')
            return None

    def _build_headers(self) -> dict:
        """Build request headers with auth token."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.auth_token}",
            "Origin": "https://platform.stratascratch.com",
            "Referer": "https://platform.stratascratch.com/",
        }

    def _build_list_variables(self, offset: int) -> dict:
        """Build variables for the list query."""
        return {
            "first": self.page_size,
            "offset": offset,
            "orderField": "-id",
            "q": None,
            "questionTypes": self.question_types,
            "difficulties": self.difficulties,
            "companies": self.companies,
            "industries": [],
            "jobPositions": self.job_positions,
        }

    def _extract_slugs_from_edges(self, edges: list) -> List[dict]:
        """Extract slug info from GraphQL edges."""
        results = []
        for edge in edges:
            node = edge.get('node', {})
            url = node.get('url', '')
            # URL format: /technical/2546-p-value-power-and-sample-size-in-ab-testing
            slug = url.split('/technical/')[-1] if '/technical/' in url else ''
            if slug:
                results.append({
                    'slug': slug,
                    'id': node.get('id'),
                    'is_freemium': node.get('isFreemium', False),
                })
        return results

    def _map_question_type_to_topic(self, question_type: str) -> str:
        """Map StrataScratch questionType to our topic categories."""
        qt = question_type.lower().strip()
        mapping = {
            'ai product': 'AI',
            'machine learning': 'ML',
            'statistics': 'Data Science',
            'probability': 'Data Science',
            'system design': 'System Design',
            'data science': 'Data Science',
            'analytics': 'Data Science',
            'python': 'Data Science',
            'sql': 'Data Science',
        }
        return mapping.get(qt, 'AI')
