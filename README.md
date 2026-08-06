# Coffee Analytics Platform

A social media data scraper and analytics dashboard for coffee businesses. This platform collects public posts from Reddit, Twitter/X, and Instagram that mention coffee-related keywords, analyzes the data, and displays actionable business insights on an interactive dashboard.

---

## Project Structure

```
coffee_analytics/
├── main.py                      # Application entry point
├── config.py                    # Configuration and settings
├── models.py                    # SQLAlchemy database models
├── database.py                  # Database service layer
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
│
├── scraper/                     # Data collection module
│   ├── orchestrator.py          # Scraping coordinator
│   ├── reddit_scraper.py        # Reddit API scraper
│   ├── twitter_scraper.py       # Twitter/X API scraper
│   └── instagram_scraper.py     # Instagram public page scraper
│
├── processor/                   # Data processing module
│   ├── pipeline.py              # Processing orchestrator
│   ├── sentiment.py             # Sentiment analysis (VADER + custom rules)
│   ├── drink_extractor.py       # Drink type & age group extraction
│   └── analytics.py             # Dashboard insight computation
│
├── api/                         # FastAPI backend
│   └── app.py                   # API endpoints and server
│
├── dashboard/                   # Frontend dashboard
│   ├── templates/
│   │   └── dashboard.html       # Main dashboard template
│   └── static/
│       ├── css/
│       │   └── style.css        # Dashboard styles
│       └── js/
│           └── dashboard.js     # Chart rendering and interactivity
│
├── data/                        # SQLite database storage
│
└── tests/                       # Test suite
    └── test_platform.py
```

---

## Quick Start

### 1. Install Dependencies

```bash
cd coffee_analytics
pip3 install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your API credentials (optional — the platform works with mock data if no credentials are provided):

| Variable | Description | Required |
|----------|-------------|----------|
| `REDDIT_CLIENT_ID` | Reddit API client ID | No |
| `REDDIT_CLIENT_SECRET` | Reddit API client secret | No |
| `TWITTER_BEARER_TOKEN` | Twitter/X API bearer token | No |
| `DATABASE_URL` | Database connection string | No (defaults to SQLite) |

### 3. Run the Application

```bash
python3 main.py
```

The dashboard will be available at **http://localhost:8000** and API documentation at **http://localhost:8000/docs**.

### 4. Run Tests

```bash
python3 -m pytest tests/ -v
```

---

## Features

### Data Collection

The platform scrapes public social media posts from three sources:

| Source | Method | Keywords |
|--------|--------|----------|
| Reddit | PRAW API (search across 14 coffee subreddits) | 20+ coffee terms |
| Twitter/X | v2 Search API (recent tweets) | 20+ coffee terms |
| Instagram | Public hashtag page scraping | 20 hashtags |

When API credentials are not configured, the platform generates realistic mock data for demonstration and testing.

### Data Processing

Each post goes through a multi-stage pipeline:

1. **Sentiment Analysis** — VADER-based analysis enhanced with coffee-specific vocabulary and emoji detection
2. **Drink Type Extraction** — Pattern matching identifies 18+ coffee drink types from post text
3. **Age Group Estimation** — Bio/text analysis estimates user age demographics
4. **Keyword Matching** — Extracts all coffee-related keywords mentioned

### Analytics Dashboard

The dashboard displays 10 interactive visualizations:

| Chart | Type | Data Source |
|-------|------|-------------|
| Most Popular Drinks | Bar Chart | Drink type extraction |
| Sentiment Breakdown | Doughnut Chart | Sentiment analysis |
| Peak Drinking Hours | Line Chart | Hour-of-day analysis |
| Day of Week Patterns | Bar Chart | Day-of-week analysis |
| Activity Heatmap | Plotly Heatmap | Day × Hour grid |
| Age Group Distribution | Doughnut Chart | Age estimation |
| Trending Keywords | Tag Cloud | Keyword extraction |
| Engagement by Drink | Horizontal Bar | Engagement scores |
| Source Breakdown | Grouped Bar | Platform statistics |
| Sentiment Over Time | Area Chart | Time-series data |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/summary` | GET | Overall analytics summary |
| `/api/popular-drinks` | GET | Most popular drink types |
| `/api/peak-hours` | GET | Peak drinking hour patterns |
| `/api/sentiment` | GET | Sentiment breakdown |
| `/api/age-distribution` | GET | Age group distribution |
| `/api/trending-keywords` | GET | Trending keywords |
| `/api/engagement-by-drink` | GET | Engagement by drink type |
| `/api/heatmap` | GET | Day × Hour heatmap data |
| `/api/dashboard-data` | GET | All data in one response |
| `/api/scrape` | POST | Trigger data collection |
| `/api/posts` | GET | Browse recent posts |
| `/api/search` | POST | Search posts by keyword |
| `/api/health` | GET | Health check |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Dashboard (Frontend)                   │
│              HTML/CSS/JS + Chart.js + Plotly             │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP API
┌───────────────────────▼─────────────────────────────────┐
│                  FastAPI Server (Backend)                 │
│              Routes, CORS, Templates, Static Files       │
└───────────────────────┬─────────────────────────────────┘
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Analytics   │ │   Pipeline   │ │   Database  │
│  Processor   │ │  Processor   │ │   Service   │
│  (Insights)  │ │  (Sentiment, │ │  (SQLite)   │
│             │ │  Extraction) │ │             │
└─────────────┘ └──────┬──────┘ └─────────────┘
                       │
┌──────────────────────▼─────────────────────────────────┐
│                   Scraper Orchestrator                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐         │
│  │  Reddit   │  │  Twitter │  │  Instagram   │         │
│  │  Scraper  │  │  Scraper │  │   Scraper    │         │
│  └──────────┘  └──────────┘  └──────────────┘         │
└────────────────────────────────────────────────────────┘
```

---

## Ethical Considerations

This platform adheres to strict ethical guidelines:

- **Public data only** — Only collects publicly available posts; never uses login scraping
- **Rate limit compliance** — Respects API rate limits with appropriate delays between requests
- **Privacy protection** — Usernames are anonymized; no personal information is stored
- **Aggregate insights only** — The dashboard displays only aggregate patterns, never individual user data
- **No data selling** — All collected data is used solely for the coffee business owner's insights

---

## Configuration

Key configuration options in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_POSTS_PER_SOURCE` | 100 | Maximum posts to collect per source |
| `SCRAPE_INTERVAL_HOURS` | 6 | Minimum hours between scrapes |
| `DASHBOARD_PORT` | 8000 | Server port |
| `COFFEE_KEYWORDS` | 20 terms | Keywords to search for |
| `DEBUG_MODE` | true | Enable hot-reload |

---

## Extending the Platform

### Adding New Data Sources

1. Create a new scraper class in `scraper/`
2. Implement the `scrape()` method returning a list of post dictionaries
3. Add the scraper to the orchestrator in `scraper/orchestrator.py`

### Adding New Analytics

1. Add a new method to `processor/analytics.py`
2. Create a corresponding API endpoint in `api/app.py`
3. Add a chart component to `dashboard/static/js/dashboard.js`

### Custom Coffee Keywords

Edit the `COFFEE_KEYWORDS` list in `config.py` to add or remove tracked terms.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, Uvicorn |
| Scraping | PRAW, Requests, BeautifulSoup |
| NLP | VADER Sentiment, custom rules |
| Database | SQLite, SQLAlchemy ORM |
| Frontend | HTML5, CSS3, Vanilla JS |
| Charts | Chart.js 4.x, Plotly.js |
| Testing | pytest, pytest-asyncio |

---

## License

This project is provided as-is for educational and business use.
