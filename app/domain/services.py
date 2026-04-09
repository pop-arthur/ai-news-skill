from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.domain.entities import Article


AI_KEYWORDS = (
    "ai",
    "artificial intelligence",
    "llm",
    "large language model",
    "large language models",
    "machine learning",
    "ml",
    "gpt",
    "genai",
    "generative ai",
    "neural network",
    "deep learning",
    "anthropic",
    "openai",
    "claude",
    "chatgpt",
    "gemini",
    "llama",
    "mistral",
)


class ArticleFilter:
    """Encapsulates article relevance and user-supplied filtering rules."""

    def __init__(self, keywords: tuple[str, ...] = AI_KEYWORDS) -> None:
        self._keywords = tuple(keyword.casefold() for keyword in keywords)

    def is_ai_related(self, article: Article) -> bool:
        haystack = f"{article.title} {article.description}".casefold()
        return any(keyword in haystack for keyword in self._keywords)

    def matches_query(self, article: Article, query: str | None) -> bool:
        if not query:
            return True
        normalized_query = query.casefold().strip()
        haystack = f"{article.title} {article.description}".casefold()
        return normalized_query in haystack

    def matches_source(self, article: Article, source: str | None) -> bool:
        if not source:
            return True
        return article.source.casefold() == source.casefold().strip()


class ArticleDeduplicator:
    """Removes obvious duplicates using URL equality and title similarity."""

    def __init__(self, similarity_threshold: float = 0.92) -> None:
        self._similarity_threshold = similarity_threshold

    def deduplicate(self, articles: list[Article]) -> list[Article]:
        deduped: list[Article] = []
        seen_urls: set[str] = set()

        for article in articles:
            normalized_url = article.url.strip().lower()
            if normalized_url in seen_urls:
                continue

            if any(self._are_titles_similar(article.title, existing.title) for existing in deduped):
                continue

            if normalized_url:
                seen_urls.add(normalized_url)
            deduped.append(article)

        return deduped

    def _are_titles_similar(self, first: str, second: str) -> bool:
        normalized_first = self._normalize_title(first)
        normalized_second = self._normalize_title(second)
        if not normalized_first or not normalized_second:
            return False
        return (
            SequenceMatcher(None, normalized_first, normalized_second).ratio()
            >= self._similarity_threshold
        )

    @staticmethod
    def _normalize_title(value: str) -> str:
        return re.sub(r"\W+", " ", value).strip().casefold()
