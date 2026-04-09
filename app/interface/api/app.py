from __future__ import annotations

from fastapi import FastAPI

from app.interface.api.routes import router


app = FastAPI(title="AI News Aggregator", version="0.1.0")
app.include_router(router)
