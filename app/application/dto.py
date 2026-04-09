from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class NewsQuery:
    q: str | None = None
    source: str | None = None
    limit: int = 20


@dataclass(frozen=True, slots=True)
class NewsResultItem:
    id: str
    title: str
    description: str
    url: str
    source: str
    published_at: datetime


@dataclass(frozen=True, slots=True)
class SourceError:
    source: str
    message: str


@dataclass(frozen=True, slots=True)
class NewsResult:
    items: list[NewsResultItem]
    errors: list[SourceError]
