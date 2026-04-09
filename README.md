# AI News Aggregator

AI News Aggregator is a small backend service that fetches news from multiple external feeds, normalizes the data into a single model, filters it for AI-related content, removes duplicates, sorts by publication time, and exposes the result through a REST API.

The project is intentionally structured as a Clean Architecture MVP. The main goal is to keep business rules independent from frameworks and external providers, so the aggregation logic stays easy to test and easy to extend.

## Quick Overview of Clean Architecture

Clean Architecture separates the system into layers with clear responsibilities. The inner layers contain business rules. The outer layers contain technical details like HTTP, RSS parsing, and FastAPI.

The dependency direction always points inward:

- Interface layer depends on application layer
- Infrastructure layer depends on domain and application layer contracts
- Application layer depends on domain layer
- Domain layer depends on nothing external

That means the core news logic does not need to know whether articles came from RSS, a public API, or a mock provider, and it does not need to know whether results are returned through FastAPI, a CLI command, or a background job.

## Layers in This Project

### Domain layer

The domain layer defines the business vocabulary and business rules.

- `app/domain/entities.py`
  Defines the `Article` entity, which is the normalized representation used throughout the system.
- `app/domain/interfaces.py`
  Defines the `NewsSource` contract. Any external provider must implement this interface.
- `app/domain/services.py`
  Contains pure business logic:
  filtering articles by AI-related keywords and deduplicating similar articles.

What belongs here:

- Article model
- Relevance rules
- Deduplication rules

What does not belong here:

- FastAPI code
- HTTP requests
- RSS parsing
- Environment variable loading

### Application layer

The application layer coordinates the domain rules to deliver a concrete use case.

- `app/application/dto.py`
  Defines request and response DTOs used by the use case.
- `app/application/use_cases.py`
  Implements `GetNewsUseCase`, the core orchestration flow of the system.

Responsibilities of the application layer:

- Fetch from multiple sources in parallel
- Collect partial failures without failing the whole request
- Apply domain filtering
- Apply deduplication
- Sort results
- Enforce the requested result limit

This layer should read like a business workflow, not like framework glue.

### Infrastructure layer

The infrastructure layer contains concrete adapters for the outside world.

- `app/infrastructure/http.py`
  Standard-library HTTP client adapter.
- `app/infrastructure/rss_parser.py`
  Parses RSS and Atom XML and turns them into normalized `Article` entities.
- `app/infrastructure/news_sources.py`
  Concrete `NewsSource` implementation for RSS feeds.
- `app/infrastructure/config.py`
  Loads runtime configuration such as source URLs and timeouts.
- `app/infrastructure/logging.py`
  Configures application logging.
- `app/infrastructure/container.py`
  Wires implementations together and builds the use case.

This is the layer most likely to change when you swap technologies or external providers.

### Interface layer

The interface layer exposes the use case to clients.

- `app/interface/api/app.py`
  Builds the FastAPI app.
- `app/interface/api/routes.py`
  Exposes `GET /news`.
- `app/interface/api/schemas.py`
  Defines request and response API shapes.
- `app/interface/api/dependencies.py`
  Provides dependency wiring for FastAPI.

This layer should stay thin. It translates HTTP input into a use-case call and then maps the use-case result into an HTTP response.

## Overall Pipeline

The end-to-end pipeline for `GET /news` looks like this:

1. A client calls `GET /news` with optional `q`, `source`, and `limit` query parameters.
2. The FastAPI route creates a `NewsQuery` object and calls `GetNewsUseCase`.
3. The use case asks all configured `NewsSource` implementations to fetch articles in parallel.
4. Each source uses the infrastructure HTTP client with a timeout to fetch its feed.
5. RSS or Atom payloads are parsed and normalized into domain `Article` objects.
6. The use case applies AI-related filtering on title plus description.
7. The use case applies optional user filters such as `q` and `source`.
8. Duplicate or near-duplicate articles are removed.
9. Remaining articles are sorted by `published_at` in descending order.
10. The API returns the final list and includes any per-source errors as partial-failure metadata.

In short:

`external feeds -> infrastructure adapters -> normalized Article objects -> use case -> API response`

## Why `fetch_ai_news.py` Exists

`fetch_ai_news.py` is the CLI entrypoint for the same aggregation pipeline used by the API.

Its purpose is to provide a lightweight way to run the aggregator without starting FastAPI. That makes it useful for:

- local smoke testing
- terminal-based inspection of fetched articles
- automation hooks
- debugging source configuration

Instead of reimplementing any news logic, `fetch_ai_news.py` reuses the same application and infrastructure wiring as the REST API. This is important because it keeps behavior consistent across entrypoints.

What `fetch_ai_news.py` does:

1. Builds the dependency container
2. Creates the `GetNewsUseCase`
3. Executes the use case with a default limit of 10
4. Converts the result DTOs into JSON-friendly dictionaries
5. Prints the aggregated payload to stdout

What `fetch_ai_news.py` does not do:

- It does not fetch RSS directly by itself
- It does not contain business filtering logic
- It does not deduplicate articles by itself
- It does not bypass the architecture

That design keeps the CLI adapter very small and makes it a good example of how additional interfaces should be added in the future.

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

## API

### `GET /news`

Query params:

- `q`: optional free-text filter applied to title and description
- `source`: optional exact source filter
- `limit`: optional result limit, bounded by configured max

Example:

```bash
curl "http://127.0.0.1:8000/news?source=Google%20News&limit=5"
```

Response shape:

```json
{
  "items": [
    {
      "id": "65949220d940c779",
      "title": "Claude, OpenClaw and the new reality: AI agents are here — and so is the chaos - VentureBeat",
      "description": "Claude, OpenClaw and the new reality: AI agents are here — and so is the chaos VentureBeat",
      "url": "https://news.google.com/...",
      "source": "VentureBeat AI",
      "published_at": "2026-04-09T04:51:37+00:00"
    }
  ],
  "count": 1,
  "errors": []
}
```

## Configuration

Environment variables:

- `NEWS_REQUEST_TIMEOUT_SECONDS`
  Per-source timeout in seconds
- `NEWS_DEFAULT_LIMIT`
  Default limit when `limit` is not provided
- `NEWS_MAX_LIMIT`
  Maximum allowed limit for the API
- `NEWS_SOURCES`
  JSON array of source objects with `name` and `url`

Example:

```bash
export NEWS_SOURCES='[
  {"name": "Google News", "url": "https://news.google.com/rss/search?q=AI&hl=en-US&gl=US&ceid=US:en"},
  {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/"},
  {"name": "VentureBeat AI", "url": "https://news.google.com/rss/search?q=site:venturebeat.com+AI&hl=en-US&gl=US&ceid=US:en"}
]'
```

## Running the Project

1. Create or activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the API:

```bash
uvicorn main:app --reload
```

4. Query the API:

```bash
curl "http://127.0.0.1:8000/news?limit=5"
```

5. Or run the CLI adapter:

```bash
python fetch_ai_news.py
```

## Notes and Edge Cases

- If one external source fails, the service still returns results from the other sources.
- Empty or malformed feed items are skipped during normalization.
- Duplicate articles are removed using URL equality and title similarity.
- Source requests are executed concurrently.
- If no articles match after filtering, the API returns an empty `items` list rather than an error.
