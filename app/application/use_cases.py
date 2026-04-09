from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.application.dto import NewsQuery, NewsResult, NewsResultItem, SourceError
from app.domain.entities import Article
from app.domain.interfaces import NewsSource
from app.domain.services import ArticleDeduplicator, ArticleFilter


class GetNewsUseCase:
    def __init__(
        self,
        sources: list[NewsSource],
        article_filter: ArticleFilter,
        deduplicator: ArticleDeduplicator,
        logger: logging.Logger,
    ) -> None:
        self._sources = sources
        self._article_filter = article_filter
        self._deduplicator = deduplicator
        self._logger = logger

    def execute(self, query: NewsQuery) -> NewsResult:
        raw_articles, errors = self._fetch_from_sources()

        filtered_articles = [
            article
            for article in raw_articles
            if self._article_filter.is_ai_related(article)
            and self._article_filter.matches_query(article, query.q)
            and self._article_filter.matches_source(article, query.source)
        ]

        deduped_articles = self._deduplicator.deduplicate(filtered_articles)
        deduped_articles.sort(key=lambda article: article.published_at, reverse=True)

        limited_articles = deduped_articles[: max(query.limit, 0)]
        return NewsResult(
            items=[self._to_result_item(article) for article in limited_articles],
            errors=errors,
        )

    def _fetch_from_sources(self) -> tuple[list[Article], list[SourceError]]:
        if not self._sources:
            return [], []

        articles: list[Article] = []
        errors: list[SourceError] = []

        with ThreadPoolExecutor(max_workers=len(self._sources)) as executor:
            future_to_source = {
                executor.submit(source.fetch): source.source_name for source in self._sources
            }

            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    articles.extend(future.result())
                except Exception as exc:
                    self._logger.exception("Failed to fetch source %s", source_name)
                    errors.append(SourceError(source=source_name, message=str(exc)))

        return articles, errors

    @staticmethod
    def _to_result_item(article: Article) -> NewsResultItem:
        return NewsResultItem(
            id=article.id,
            title=article.title,
            description=article.description,
            url=article.url,
            source=article.source,
            published_at=article.published_at,
        )
