from __future__ import annotations

import logging
import urllib.error
import xml.etree.ElementTree as ET

from app.domain.entities import Article
from app.domain.interfaces import NewsSource
from app.infrastructure.http import HttpClient
from app.infrastructure.rss_parser import parse_rss_articles


class RssNewsSource(NewsSource):
    def __init__(
        self,
        source_name: str,
        url: str,
        http_client: HttpClient,
        timeout_seconds: float,
        logger: logging.Logger,
    ) -> None:
        self._source_name = source_name
        self._url = url
        self._http_client = http_client
        self._timeout_seconds = timeout_seconds
        self._logger = logger

    @property
    def source_name(self) -> str:
        return self._source_name

    def fetch(self) -> list[Article]:
        try:
            payload = self._http_client.get(self._url, timeout=self._timeout_seconds)
            return parse_rss_articles(payload, self._source_name)
        except (urllib.error.URLError, TimeoutError, ET.ParseError, ValueError) as exc:
            self._logger.error("Source fetch failed for %s: %s", self._source_name, exc)
            raise RuntimeError(f"source fetch failed: {exc}") from exc
