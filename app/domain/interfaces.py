from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities import Article


class NewsSource(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def fetch(self) -> list[Article]:
        raise NotImplementedError
