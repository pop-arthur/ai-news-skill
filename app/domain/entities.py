from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Article:
    id: str
    title: str
    description: str
    url: str
    source: str
    published_at: datetime
