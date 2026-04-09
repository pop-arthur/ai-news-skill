from __future__ import annotations

import json
import sys
from dataclasses import asdict

from app.application.dto import NewsQuery
from app.infrastructure.container import Container


def main() -> int:
    use_case = Container().build_get_news_use_case()
    result = use_case.execute(NewsQuery(limit=10))
    payload = {
        "items": [
            {
                **asdict(item),
                "published_at": item.published_at.isoformat(),
            }
            for item in result.items
        ],
        "errors": [asdict(error) for error in result.errors],
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
