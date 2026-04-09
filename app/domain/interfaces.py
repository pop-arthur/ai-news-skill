from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities import Article


class NewsSource(ABC):
    """Abstraction for any external news provider."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def fetch(self) -> list[Article]:
        """Fetch and normalize articles from the external provider."""
        raise NotImplementedError
