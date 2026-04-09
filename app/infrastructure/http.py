from __future__ import annotations

import urllib.request
from typing import Protocol


class HttpClient(Protocol):
    def get(self, url: str, timeout: float) -> bytes:
        ...


class UrllibHttpClient:
    def __init__(self, user_agent: str = "ai-news-aggregator/1.0") -> None:
        self._user_agent = user_agent

    def get(self, url: str, timeout: float) -> bytes:
        request = urllib.request.Request(url, headers={"User-Agent": self._user_agent})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
