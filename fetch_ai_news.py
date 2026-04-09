from __future__ import annotations

"""CLI adapter for the AI News Aggregator.

This module intentionally stays very small. Its job is not to implement any
aggregation logic by itself, but to reuse the same Clean Architecture pipeline
that powers the FastAPI endpoint.

Flow:
1. Build the dependency container
2. Resolve the main news use case
3. Execute the use case with a small default limit
4. Convert the result into JSON-serializable data
5. Print the payload to stdout
"""

import json
import sys
from dataclasses import asdict

from app.application.dto import NewsQuery
from app.infrastructure.container import Container


def _serialize_result() -> dict[str, object]:
    """Execute the aggregation pipeline and convert the result to plain JSON data.

    The use case returns dataclass-based DTOs containing native Python datetime
    objects. This helper converts them into a JSON-friendly structure without
    leaking serialization logic into the application layer.
    """

    # Reuse the shared dependency wiring so CLI and API stay behaviorally aligned.
    use_case = Container().build_get_news_use_case()
    result = use_case.execute(NewsQuery(limit=10))
    return {
        "items": [
            {
                **asdict(item),
                "published_at": item.published_at.isoformat(),
            }
            for item in result.items
        ],
        "errors": [asdict(error) for error in result.errors],
    }


def main() -> int:
    """Run the CLI entrypoint and print aggregated AI news as formatted JSON."""
    payload = _serialize_result()

    # Pretty-printing is intentional here because this file is meant for humans,
    # shell scripts, and quick local inspection during development.
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
