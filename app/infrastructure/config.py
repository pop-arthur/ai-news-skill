from __future__ import annotations

import json
import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceConfig:
    name: str
    url: str


@dataclass(frozen=True, slots=True)
class Settings:
    request_timeout_seconds: float = 10.0
    default_limit: int = 20
    max_limit: int = 100
    sources: tuple[SourceConfig, ...] = ()


DEFAULT_SOURCES = (
    SourceConfig(
        name="Google News",
        url=(
            "https://news.google.com/rss/search?"
            "q=%28%22artificial+intelligence%22+OR+AI+OR+LLM+OR+%22machine+learning%22%29+when%3A7d"
            "&hl=en-US&gl=US&ceid=US%3Aen"
        ),
    ),
    SourceConfig(
        name="MIT Technology Review",
        url="https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    ),
    SourceConfig(
        name="VentureBeat AI",
        url=(
            "https://news.google.com/rss/search?"
            "q=site%3Aventurebeat.com+%28AI+OR+LLM+OR+%22machine+learning%22%29+when%3A30d"
            "&hl=en-US&gl=US&ceid=US%3Aen"
        ),
    ),
)


def load_settings() -> Settings:
    timeout = float(os.getenv("NEWS_REQUEST_TIMEOUT_SECONDS", "10"))
    default_limit = int(os.getenv("NEWS_DEFAULT_LIMIT", "20"))
    max_limit = int(os.getenv("NEWS_MAX_LIMIT", "100"))

    sources_env = os.getenv("NEWS_SOURCES")
    if not sources_env:
        return Settings(
            request_timeout_seconds=timeout,
            default_limit=default_limit,
            max_limit=max_limit,
            sources=DEFAULT_SOURCES,
        )

    raw_sources = json.loads(sources_env)
    parsed_sources = tuple(
        SourceConfig(name=source["name"], url=source["url"]) for source in raw_sources
    )
    return Settings(
        request_timeout_seconds=timeout,
        default_limit=default_limit,
        max_limit=max_limit,
        sources=parsed_sources,
    )
