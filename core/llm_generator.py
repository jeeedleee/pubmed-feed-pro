"""LLM-based PubMed query generator."""

from typing import List

from openai import AsyncOpenAI

from core.config import get_config


class QueryGenerator:
    """Generate PubMed search queries from natural language interests."""

    SYSTEM_PROMPT = """You are an expert in medical literature search and PubMed query syntax.

Your task is to convert natural language descriptions of research interests into optimized PubMed search queries.

Guidelines:
1. Translate Chinese concepts to English medical terminology
2. Use MeSH terms when appropriate
3. Include both exact phrases (in quotes) and related keywords
4. Use Boolean operators (AND, OR, NOT) effectively
5. Add field tags like [Title/Abstract], [MeSH Terms] when helpful
6. Keep the query focused but comprehensive
7. Target healthcare and medicine research areas

Examples:
Input: "AI in cancer diagnosis"
Output: ("artificial intelligence" OR "machine learning" OR "deep learning") AND (cancer OR neoplasm OR tumor) AND (diagnosis OR detection OR screening)[Title/Abstract]

Input: "LLM在医疗影像诊断中的应用"
Output: ("large language model" OR LLM OR "transformer") AND ("medical imaging" OR radiology OR "diagnostic imaging") AND (diagnosis OR detection)[Title/Abstract]

Input: "大语言模型在药物发现中的研究"
Output: ("large language model" OR LLM OR "foundation model") AND ("drug discovery" OR "drug development" OR "pharmaceutical research")[Title/Abstract]

Return ONLY the query string, no explanation. Do not use Chinese characters in the query."""

    def __init__(self):
        config = get_config()
        self.client = AsyncOpenAI(
            base_url=config.llm.base_url, api_key=config.llm.api_key
        )
        self.model = config.llm.model

    async def generate_query(self, interest: str) -> str:
        """Generate PubMed query from natural language interest."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": interest},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Fallback to basic query if LLM fails
            return f'({interest})[Title/Abstract]'

    async def generate_queries(self, interests: List[str]) -> List[str]:
        """Generate queries for multiple interests."""
        queries = []
        for interest in interests:
            query = await self.generate_query(interest)
            queries.append(query)
        return queries

    async def combine_queries(self, queries: List[str]) -> str:
        """Combine multiple queries with OR operator."""
        if len(queries) == 1:
            return queries[0]
        return " OR ".join(f"({q})" for q in queries)
