from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.application.dto import NewsQuery
from app.application.use_cases import GetNewsUseCase
from app.interface.api.dependencies import get_container, get_news_use_case
from app.interface.api.schemas import (
    NewsResponse,
    NewsResponseItem,
    NewsSourceErrorResponse,
)


router = APIRouter()


@router.get("/news", response_model=NewsResponse)
def get_news(
    q: str | None = Query(default=None),
    source: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=0),
    use_case: GetNewsUseCase = Depends(get_news_use_case),
) -> NewsResponse:
    settings = get_container().settings
    effective_limit = settings.default_limit if limit is None else min(limit, settings.max_limit)
    result = use_case.execute(NewsQuery(q=q, source=source, limit=effective_limit))

    return NewsResponse(
        items=[
            NewsResponseItem(
                id=item.id,
                title=item.title,
                description=item.description,
                url=item.url,
                source=item.source,
                published_at=item.published_at,
            )
            for item in result.items
        ],
        count=len(result.items),
        errors=[
            NewsSourceErrorResponse(source=error.source, message=error.message)
            for error in result.errors
        ],
    )
