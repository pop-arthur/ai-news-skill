from __future__ import annotations

from functools import lru_cache

from app.application.use_cases import GetNewsUseCase
from app.infrastructure.container import Container


@lru_cache(maxsize=1)
def get_container() -> Container:
    return Container()


def get_news_use_case() -> GetNewsUseCase:
    return get_container().build_get_news_use_case()
