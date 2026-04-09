# AI News Aggregator

Production-ready MVP for aggregating AI, LLM, and ML news from multiple configurable sources using Clean Architecture.

## Clean Architecture Layers

### Domain layer

The domain layer contains the core business model and business rules.

- `app/domain/entities.py`: defines the central `Article` entity used everywhere else.
- `app/domain/interfaces.py`: defines the `NewsSource` abstraction so business logic depends on contracts, not concrete providers.
- `app/domain/services.py`: contains pure business rules for AI keyword filtering and article deduplication.

This layer does not know anything about FastAPI, HTTP clients, RSS parsing, or environment configuration.

### Application layer

The application layer orchestrates the domain logic to fulfill a use case.

- `app/application/dto.py`: defines request and response data structures for use cases.
- `app/application/use_cases.py`: implements the `GetNewsUseCase`, which fetches from sources in parallel, applies filtering, deduplication, sorting, and returns partial results plus source errors.

This layer coordinates work, but it still depends only on abstractions and domain rules rather than framework details.

### Infrastructure layer

The infrastructure layer contains technical implementations for external concerns.

- `app/infrastructure/http.py`: concrete HTTP client implementation using the standard library.
- `app/infrastructure/rss_parser.py`: converts RSS and Atom payloads into normalized domain `Article` objects.
- `app/infrastructure/news_sources.py`: concrete `NewsSource` implementation for RSS feeds.
- `app/infrastructure/config.py`: loads configurable source and timeout settings.
- `app/infrastructure/logging.py`: configures logging.
- `app/infrastructure/container.py`: wires concrete implementations to application use cases.

This is where external systems are integrated, while the inner layers stay framework-agnostic.

### Interface layer

The interface layer exposes the system to the outside world.

- `app/interface/api/routes.py`: defines the REST endpoint `GET /news`.
- `app/interface/api/schemas.py`: defines API request and response schemas.
- `app/interface/api/dependencies.py`: provides dependency wiring for FastAPI.
- `app/interface/api/app.py`: creates the FastAPI application.

Controllers in this layer stay thin: they receive HTTP input, call the use case, and map the result to an API response.

## Project Structure

```text
.
├── app
│   ├── application
│   │   ├── dto.py
│   │   └── use_cases.py
│   ├── domain
│   │   ├── entities.py
│   │   ├── interfaces.py
│   │   └── services.py
│   ├── infrastructure
│   │   ├── config.py
│   │   ├── container.py
│   │   ├── http.py
│   │   ├── logging.py
│   │   ├── news_sources.py
│   │   └── rss_parser.py
│   └── interface
│       └── api
│           ├── app.py
│           ├── dependencies.py
│           ├── routes.py
│           └── schemas.py
├── fetch_ai_news.py
├── main.py
├── README.md
└── requirements.txt
```

## Run

1. Create or activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the API:

```bash
uvicorn main:app --reload
```

4. Call the API:

```bash
curl "http://127.0.0.1:8000/news?limit=5"
```

## Config

- `NEWS_REQUEST_TIMEOUT_SECONDS`: per-source timeout
- `NEWS_DEFAULT_LIMIT`: default `/news` limit
- `NEWS_MAX_LIMIT`: max allowed `/news` limit
- `NEWS_SOURCES`: JSON array of objects with `name` and `url`

Example:

```bash
export NEWS_SOURCES='[
  {"name": "Google News", "url": "https://news.google.com/rss/search?q=AI&hl=en-US&gl=US&ceid=US:en"},
  {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/"}
]'
```
