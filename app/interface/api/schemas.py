from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NewsResponseItem(BaseModel):
    id: str
    title: str
    description: str
    url: str
    source: str
    published_at: datetime


class NewsSourceErrorResponse(BaseModel):
    source: str
    message: str


class NewsResponse(BaseModel):
    items: list[NewsResponseItem] = Field(default_factory=list)
    count: int
    errors: list[NewsSourceErrorResponse] = Field(default_factory=list)
