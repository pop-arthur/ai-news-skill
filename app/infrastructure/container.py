from __future__ import annotations

from app.application.use_cases import GetNewsUseCase
from app.domain.services import ArticleDeduplicator, ArticleFilter
from app.infrastructure.config import Settings, load_settings
from app.infrastructure.http import UrllibHttpClient
from app.infrastructure.logging import configure_logging
from app.infrastructure.news_sources import RssNewsSource


class Container:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        self.logger = configure_logging()
        self.http_client = UrllibHttpClient()

    def build_get_news_use_case(self) -> GetNewsUseCase:
        sources = [
            RssNewsSource(
                source_name=source.name,
                url=source.url,
                http_client=self.http_client,
                timeout_seconds=self.settings.request_timeout_seconds,
                logger=self.logger,
            )
            for source in self.settings.sources
        ]
        return GetNewsUseCase(
            sources=sources,
            article_filter=ArticleFilter(),
            deduplicator=ArticleDeduplicator(),
            logger=self.logger,
        )
