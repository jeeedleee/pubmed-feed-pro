# PubMed Papers Feed - Agent Guide

## Project Overview

PubMed 文章推送工具 (PubMed Papers Feed) is an intelligent PubMed literature aggregation and social media content generation tool. It leverages Large Language Models (LLMs) to:

1. Convert natural language research interests into optimized PubMed search queries
2. Fetch recent papers from PubMed E-utilities API
3. Generate platform-specific content for Chinese social media (小红书/Xiaohongshu and 微信公众号/WeChat)
4. Manage articles and reports through a web interface

## Technology Stack

### Backend
- **Framework**: FastAPI (async Python web framework)
- **Server**: Uvicorn (ASGI server with hot reload)
- **Database**: SQLite with SQLAlchemy ORM
- **Scheduling**: APScheduler (cron-based job scheduling)

### External APIs
- **LLM**: OpenAI API-compatible services (GPT-4, Claude, local models via Ollama, etc.)
- **PubMed**: NCBI E-utilities API (esearch.fcgi, efetch.fcgi)

### Frontend
- **Templates**: Jinja2 (server-side rendering)
- **Static Assets**: Plain CSS/JS (no frontend framework)

### Dependencies
Key packages from `requirements.txt`:
- `fastapi>=0.110.0`, `uvicorn>=0.29.0` - Web framework
- `sqlalchemy>=2.0.25`, `aiosqlite>=0.19.0` - Database
- `openai>=1.30.0`, `httpx>=0.27.0` - LLM and HTTP client
- `apscheduler>=3.10.4` - Job scheduling
- `pydantic>=2.7.0` - Data validation
- `pyyaml>=6.0.1` - Configuration parsing

## Project Structure

```
pubmed_papers_feed/
├── main.py                 # Application entry point
├── config.yaml             # User configuration (not in git)
├── config.yaml.example     # Configuration template
├── requirements.txt        # Python dependencies
├── core/                   # Core business logic
│   ├── __init__.py         # Module exports
│   ├── __main__.py         # CLI entry point
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration management (Pydantic models)
│   ├── database.py         # SQLAlchemy models and database operations
│   ├── pubmed_client.py    # PubMed E-utilities API client
│   ├── llm_generator.py    # LLM-based query generation
│   ├── content_generator.py # Platform-specific content generation
│   ├── reporter.py         # Report generation and file storage
│   └── scheduler.py        # Automatic search scheduling
├── web/                    # Web interface
│   ├── app.py              # FastAPI routes and handlers
│   ├── static/             # CSS, JS, images
│   │   ├── css/
│   │   └── js/
│   └── templates/          # Jinja2 HTML templates
│       ├── dashboard.html
│       ├── config.html
│       ├── search.html
│       ├── search_history.html  # Search history page
│       ├── reports.html
│       ├── view_report.html
│       └── preview.html
└── data/                   # Data storage
    ├── pubmed.db           # SQLite database
    └── reports/            # Generated reports (YYYY-MM-DD subdirs)
```

## Module Responsibilities

### core/config.py
- Pydantic models: `LLMConfig`, `PubMedConfig`, `TemplatesConfig`, `AppConfig`
- `ConfigManager`: YAML config load/save operations
- Global singleton: `config_manager` and `get_config()` helper

### core/database.py
- SQLAlchemy declarative models: `Article`, `Report`, `SearchHistory`
- `Database` class: CRUD operations for articles, reports, and search history
- Global singleton: `db` instance
- Schema:
  - `articles`: pmid (PK), title, abstract, authors (JSON), journal, pub_date, doi, keywords (JSON), mesh_terms (JSON), fetched_at, quality_score
  - `reports`: id (PK), date, article_ids (JSON), file_paths (JSON), created_at, article_count
  - `search_history`: id (PK), query, natural_language, total_found, new_articles, created_at
- Methods:
  - `save_search_history()`: Record each search with query, natural language input, and results count
  - `get_search_history()`: Retrieve recent searches
  - `delete_search_history()`: Remove a history record

### core/pubmed_client.py
- `PubMedArticle`: Data class for article metadata
- `PubMedClient`: HTTP client for NCBI E-utilities
  - `search()`: Convert query to PMID list via esearch
  - `fetch_articles()`: Get full metadata via efetch (XML parsing)
  - `search_and_fetch()`: Combined convenience method

### core/llm_generator.py
- `QueryGenerator`: Converts natural language to PubMed queries
  - Uses system prompt with MeSH/Boolean operator guidelines
  - `generate_query()`: Single interest to query
  - `generate_queries()`: Batch processing
  - `combine_queries()`: Join with OR operator

### core/content_generator.py
- `ContentGenerator`: Creates platform-specific content via LLM
  - `generate_xiaohongshu_long()`: 200-300 characters casual tech content with emoji
  - `generate_xiaohongshu_short()`: 80-120 characters quick news format
  - `generate_wechat_long()`: 800-1200 characters professional article with statistics
  - `generate_wechat_short()`: 300-500 characters brief professional summary
  - `generate_all()`: Batch generation of all formats
  - Fallback templates for each format if LLM fails

### core/reporter.py
- `ReportGenerator`: File I/O and report organization
  - `create_report()`: Main entry point, generates 6 files (xiaohongshu/wechat x long/short_1/short_2)
  - `save_markdown()`, `save_json()`: File operations
  - `generate_daily_report()`: Creates README index
  - Report structure: `data/reports/YYYY-MM-DD/{filename}.md`

### core/scheduler.py
- `JobScheduler`: APScheduler wrapper for automatic searches
  - `start()`: Initialize and start scheduler
  - `update_schedule()`: Update cron expression at runtime
  - `_run_search()`: Scheduled job implementation

### core/cli.py
- CLI interface using `argparse`
- Commands: search (default), --preview, --config, --history, --dry-run
- `run_search()`: Async search workflow implementation

### web/app.py
- FastAPI application with routes:
  - GET `/`: Dashboard with stats
  - GET/POST `/config`: Configuration management
  - GET/POST `/search`: Search interface (supports natural language, auto-saves history)
  - POST `/generate`: Content generation
  - GET `/reports`: Report listing
  - GET `/report/{id}`: Report viewing
  - GET `/download/{id}`: File download
  - POST `/export`: Batch export
  - GET `/preview/{pmid}`: Article preview with loading animation
  - GET `/search-history`: Search history page
  - GET `/api/search-history`: JSON search history endpoint
  - DELETE `/api/search-history/{id}`: Delete history record
  - GET `/api/stats`: JSON stats endpoint
- Search page features:
  - Natural language mode: LLM converts Chinese descriptions to PubMed queries
  - Manual query mode: Direct PubMed syntax input
  - Loading indicators for search and preview operations

## Configuration

Configuration is stored in `config.yaml` with three sections:

```yaml
llm:
  base_url: "https://api.openai.com/v1"  # Any OpenAI-compatible endpoint
  api_key: "your-api-key"
  model: "gpt-4"

pubmed:
  search_days: 7          # 1-365 days
  max_results: 100        # 1-100 articles
  schedule: "0 9 * * *"   # Optional cron expression

interests:
  - "人工智能在医学影像诊断中的应用"
  - "COVID-19 疫苗的长期免疫效果研究"
```

## Running the Application

### Web Interface (Primary)
```bash
python main.py
```
- Starts FastAPI server on http://localhost:8000
- Auto-reload enabled for development
- Scheduler starts automatically if configured

### Command Line
```bash
# Search with default configuration
python -m core.cli

# Search specific interest
python -m core.cli -i "糖尿病治疗"

# Preview specific article
python -m core.cli --preview 123456

# Dry run (no LLM calls, no DB writes)
python -m core.cli --dry-run

# Show current configuration
python -m core.cli --config
```

## Code Style Guidelines

### Python Style
- Uses type hints throughout (`typing` module)
- Docstrings for all modules, classes, and public methods
- Async/await pattern for I/O operations (LLM calls, HTTP requests)
- Pydantic models for configuration validation
- SQLAlchemy 2.0 style (declarative_base, type hints)

### Naming Conventions
- `snake_case` for variables, functions, methods
- `PascalCase` for classes
- `UPPER_CASE` for constants and class-level config

### Error Handling
- Try/except blocks around external API calls (LLM, PubMed)
- Graceful fallbacks (e.g., content_generator.py fallback templates)
- Print statements for CLI feedback

## Development Workflow

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up configuration**:
   ```bash
   cp config.yaml.example config.yaml
   # Edit config.yaml with your API keys
   ```

3. **Run development server**:
   ```bash
   python main.py
   ```

4. **Test CLI**:
   ```bash
   python -m core.cli --dry-run
   ```

## Testing

No automated test suite is currently configured. Testing is done via:
- CLI dry-run mode: `python -m core.cli --dry-run`
- Web interface manual testing
- Individual module imports in Python REPL

## Data Storage

### SQLite Database (`data/pubmed.db`)
- Created automatically on first run
- Stores article metadata for deduplication
- Stores report metadata for history tracking

### Reports (`data/reports/`)
- Organized by date: `data/reports/YYYY-MM-DD/`
- Each report generates:
  - `README.md` - Index with article list
  - `xiaohongshu_long.md` - Long casual content (1 article)
  - `xiaohongshu_short_1.md`, `xiaohongshu_short_2.md` - Short casual (2 articles)
  - `wechat_long.md` - Long professional (1 article)
  - `wechat_short_1.md`, `wechat_short_2.md` - Short professional (2 articles)

## Security Considerations

1. **API Keys**: Stored in `config.yaml` (not in git by default)
2. **Database**: Local SQLite, no external connections
3. **SSL Verification**: Disabled in pubmed_client.py (`verify=False`) for compatibility
4. **No Authentication**: Web interface has no login/auth mechanism

## Common Tasks

### Adding a New Content Format
1. Add method in `core/content_generator.py`
2. Add fallback template
3. Update `generate_all()` to include new format
4. Update `core/reporter.py` to save the new format
5. Update web templates if UI changes needed

### Adding New API Endpoints
1. Add route handler in `web/app.py`
2. Use existing `templates/` directory for HTML responses
3. Follow existing pattern of `{"status": "success", ...}` for JSON responses

### Modifying Database Schema
1. Update SQLAlchemy models in `core/database.py`
2. SQLite will auto-migrate (new columns will be empty for existing rows)
3. Manual migration may be needed for data preservation

## Recent Changes

### 2024-02-09

1. **Fixed PubMed Search Bug**
   - Added missing `import urllib.parse` in `core/pubmed_client.py`

2. **Web Search Interface Enhancement**
   - Added natural language search mode (LLM auto-generates PubMed query)
   - Removed preset interests tab from search page
   - Search history automatically saved for every search

3. **Search History Feature**
   - New database table `search_history` to track all searches
   - New page `/search-history` to view and manage history
   - API endpoints: `GET /api/search-history`, `DELETE /api/search-history/{id}`
   - Navigation link added to all pages

4. **UX Improvements**
   - Added loading animation when clicking "预览文案" (Preview Content)
   - Full-screen overlay with spinner while LLM generates content

## External Resources

- PubMed E-utilities: https://www.ncbi.nlm.nih.gov/books/NBK25499/
- FastAPI Docs: https://fastapi.tiangolo.com/
- APScheduler: https://apscheduler.readthedocs.io/
