# AI News Skill

This project is a Claude Code / OpenCode skill for collecting and filtering AI news.

The main goal is not just to expose an API. The main goal is to provide a callable skill, triggered by `/news` or an equivalent command, that:

- fetches AI-related news from external sources
- filters and normalizes the results
- removes duplicates
- returns the final payload directly into the agent context

In other words, the core deliverable of this repository is `fetch_ai_news.py` and the supporting architecture around it.

## Demo

[demo.mp4](demo.mp4)

## What the Skill Does

When the skill is invoked through `/news` or a similar command:

1. The command runs `fetch_ai_news.py`
2. `fetch_ai_news.py` executes the aggregation use case
3. News is fetched from multiple configured sources
4. Articles are normalized into one internal format
5. Non-AI articles are filtered out
6. Duplicate or near-duplicate articles are removed
7. Articles are sorted by publication date
8. The result is printed as JSON so the calling agent can place it directly into context

This makes the skill useful for:

- daily AI news summaries
- agent workflows that need fresh AI-related context
- automation tasks inside Claude Code / OpenCode
- terminal-based debugging of news collection logic

## How to Run from OpenCode

This repository is designed to work well with OpenCode as a callable skill.

The intended flow is:

1. Open the project in OpenCode
2. Invoke the news command from the OpenCode command palette or slash-command flow
3. OpenCode runs the configured wrapper command
4. The wrapper command executes `fetch_ai_news.py`
5. The JSON result is returned into the agent context

In this repository, the wrapper command is:

```bash
.agents/commands/news.sh
```

That script changes into the project root and runs:

```bash
python3 fetch_ai_news.py
```

Typical local flow:

```bash
cd path-to/ai-news-skill
opencode
```

Then invoke the skill through the question on "AI news"


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

## Quick Overview of Clean Architecture

The codebase uses Clean Architecture so the skill logic stays modular and easy to extend.

The dependency direction points inward:

- interface layer depends on application layer
- infrastructure layer depends on domain and application contracts
- application layer depends on domain layer
- domain layer depends on nothing external

This matters because the core news logic should not care whether it is triggered by:

- a Claude Code command
- an OpenCode command
- a FastAPI endpoint
- a future scheduled job

The business behavior should stay the same regardless of how the skill is invoked.

## Layers in This Project

### Domain layer

The domain layer contains the business concepts and rules.

- `app/domain/entities.py`
  Defines the normalized `Article` entity.
- `app/domain/interfaces.py`
  Defines the `NewsSource` abstraction for external providers.
- `app/domain/services.py`
  Contains AI keyword filtering and deduplication rules.

This layer knows nothing about commands, FastAPI, RSS XML, or environment variables.

### Application layer

The application layer coordinates the business workflow.

- `app/application/dto.py`
  Defines use-case input and output DTOs.
- `app/application/use_cases.py`
  Implements `GetNewsUseCase`.

This is where the main orchestration happens:

- fetch from sources concurrently
- tolerate partial failures
- filter results
- deduplicate results
- sort results
- enforce the requested limit

### Infrastructure layer

The infrastructure layer contains concrete technical adapters.

- `app/infrastructure/http.py`
  HTTP client implementation using the Python standard library.
- `app/infrastructure/rss_parser.py`
  RSS and Atom parsing plus normalization into domain articles.
- `app/infrastructure/news_sources.py`
  Concrete source adapter implementing `NewsSource`.
- `app/infrastructure/config.py`
  Runtime configuration loading.
- `app/infrastructure/logging.py`
  Logging setup.
- `app/infrastructure/container.py`
  Wires the concrete pieces together.

This is the layer you extend when you add a new provider.

### Interface layer

The interface layer exposes the system to callers.

- `app/interface/api/app.py`
  FastAPI app setup.
- `app/interface/api/routes.py`
  `GET /news` endpoint.
- `app/interface/api/schemas.py`
  API response models.
- `app/interface/api/dependencies.py`
  Dependency wiring for FastAPI.

For the skill use case, the CLI command path is the primary interface. The API is a secondary interface that reuses the same core logic.

## Overall Pipeline

The core pipeline of the skill is:

`command -> fetch_ai_news.py -> container -> GetNewsUseCase -> news sources -> parser -> filter -> dedupe -> sort -> JSON output -> agent context`

Step by step:

1. A command such as `/news` invokes the skill script
2. The script runs `fetch_ai_news.py`
3. `fetch_ai_news.py` builds the dependency container
4. The container creates `GetNewsUseCase`
5. The use case fetches articles from all configured sources in parallel
6. Each source adapter downloads and parses feed data with a timeout
7. Parsed items are normalized into `Article`
8. AI-related filtering is applied to title and description
9. Duplicate content is removed
10. Articles are sorted by `published_at` descending
11. The final payload is serialized to JSON
12. The calling agent receives the output directly in its context


## How to Run the Skill Logic

Run the main skill entrypoint directly:

```bash
python fetch_ai_news.py
```

This prints JSON to stdout, which is exactly what a calling agent or wrapper command can consume.

## API

The repository also includes a FastAPI interface that reuses the same core logic.

### `GET /news`

Query params:

- `q`: optional free-text filter applied to title and description
- `source`: optional exact source filter
- `limit`: optional result limit

Example:

```bash
curl "http://127.0.0.1:8000/news?limit=5"
```

The API is useful for development and external integrations, but the skill-oriented CLI flow remains the primary use case of this project.

## Configuration

Environment variables:

- `NEWS_REQUEST_TIMEOUT_SECONDS`
  Per-source timeout in seconds
- `NEWS_DEFAULT_LIMIT`
  Default limit when `limit` is not provided
- `NEWS_MAX_LIMIT`
  Maximum allowed limit
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

## Running the Full Project

1. Create or activate a virtual environment
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the skill entrypoint:

```bash
python fetch_ai_news.py
```

4. Optionally start the API:

```bash
uvicorn main:app --reload
```
