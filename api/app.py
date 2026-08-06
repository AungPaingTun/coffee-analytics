"""
FastAPI Application
Main API server for the Coffee Analytics Platform.
Provides endpoints for data retrieval, scraping, and dashboard data.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import DASHBOARD_PORT, DEBUG_MODE, COFFEE_KEYWORDS
from models import init_db
from processor.pipeline import ProcessingPipeline
from processor.analytics import AnalyticsProcessor
from scraper.orchestrator import ScraperOrchestrator
from database import DatabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize components
app = FastAPI(
    title="Coffee Analytics API",
    description="Social media data scraper and analytics platform for coffee businesses",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")
templates = Jinja2Templates(directory="dashboard/templates")

# Service instances
pipeline = ProcessingPipeline()
analytics = AnalyticsProcessor()
scraper = ScraperOrchestrator()
db_service = DatabaseService()


# ============================================================
# Pydantic Models
# ============================================================

class ScrapeRequest(BaseModel):
    """Request model for triggering a scrape."""
    sources: Optional[List[str]] = Field(
        default=None,
        description="Specific sources to scrape: reddit, twitter, instagram"
    )
    force: bool = Field(default=False, description="Force scrape even if interval hasn't elapsed")


class SearchRequest(BaseModel):
    """Request model for searching posts."""
    query: str = Field(..., description="Search query string")
    source: Optional[str] = Field(default=None, description="Filter by source")
    limit: int = Field(default=50, ge=1, le=200)


class DateRangeRequest(BaseModel):
    """Request model for date-range queries."""
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    source: Optional[str] = Field(default=None, description="Filter by source")


# ============================================================
# Startup Event
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database and log startup."""
    init_db()
    logger.info("Coffee Analytics API started successfully.")
    logger.info(f"Server running on port {DASHBOARD_PORT}")


# ============================================================
# Dashboard Routes
# ============================================================

from starlette.requests import Request


@app.get("/", response_class=HTMLResponse)
async def dashboard_root(request: Request):
    """Serve the main dashboard page."""
    return templates.TemplateResponse(
        "dashboard.html", {"request": request}
    )


# ============================================================
# Analytics API Endpoints
# ============================================================

@app.get("/api/summary")
async def get_summary():
    """Get overall analytics summary."""
    try:
        return analytics.get_overall_summary()
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/popular-drinks")
async def get_popular_drinks(limit: int = Query(10, ge=1, le=50)):
    """Get most popular coffee drink types."""
    try:
        return analytics.get_popular_drink_types(limit=limit)
    except Exception as e:
        logger.error(f"Error getting popular drinks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/peak-hours")
async def get_peak_hours():
    """Get peak drinking hour patterns."""
    try:
        return analytics.get_peak_hours()
    except Exception as e:
        logger.error(f"Error getting peak hours: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/day-patterns")
async def get_day_patterns():
    """Get day-of-week discussion patterns."""
    try:
        return analytics.get_day_of_week_patterns()
    except Exception as e:
        logger.error(f"Error getting day patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sentiment")
async def get_sentiment():
    """Get sentiment breakdown analysis."""
    try:
        return analytics.get_sentiment_breakdown()
    except Exception as e:
        logger.error(f"Error getting sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/age-distribution")
async def get_age_distribution():
    """Get age group distribution of coffee discussions."""
    try:
        return analytics.get_age_distribution()
    except Exception as e:
        logger.error(f"Error getting age distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trending-keywords")
async def get_trending_keywords(limit: int = Query(20, ge=1, le=100)):
    """Get trending coffee keywords."""
    try:
        return analytics.get_trending_keywords(limit=limit)
    except Exception as e:
        logger.error(f"Error getting trending keywords: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/engagement-by-drink")
async def get_engagement_by_drink():
    """Get engagement scores by drink type."""
    try:
        return analytics.get_engagement_by_drink()
    except Exception as e:
        logger.error(f"Error getting engagement by drink: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/heatmap")
async def get_heatmap():
    """Get day-of-week vs hour heatmap data."""
    try:
        return analytics.get_heatmap_data()
    except Exception as e:
        logger.error(f"Error getting heatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/source-breakdown")
async def get_source_breakdown():
    """Get breakdown by social media source."""
    try:
        return analytics.get_source_breakdown()
    except Exception as e:
        logger.error(f"Error getting source breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard-data")
async def get_all_dashboard_data():
    """Get all dashboard data in a single comprehensive response."""
    try:
        return analytics.get_all_dashboard_data()
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Post Data Endpoints
# ============================================================

@app.get("/api/posts")
async def get_posts(
    limit: int = Query(100, ge=1, le=500),
    source: Optional[str] = Query(None, description="Filter by source"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    offset: int = Query(0, ge=0)
):
    """Get recent posts with optional filtering."""
    try:
        posts = db_service.get_recent_posts(limit=limit, source=source)
        
        if sentiment:
            posts = [p for p in posts if p.get("sentiment") == sentiment]
        
        # Apply offset
        posts = posts[offset:offset + limit]
        
        return {
            "posts": posts,
            "count": len(posts),
            "has_more": len(posts) == limit
        }
    except Exception as e:
        logger.error(f"Error getting posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
async def search_posts(request: SearchRequest):
    """Search posts by keyword or text."""
    try:
        results = db_service.search_posts(query=request.query, limit=request.limit)
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/posts/date-range")
async def get_posts_by_date_range(
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD"),
    source: Optional[str] = Query(None)
):
    """Get posts within a date range."""
    try:
        posts = db_service.get_posts_by_date_range(start_date, end_date, source)
        return {
            "start_date": start_date,
            "end_date": end_date,
            "posts": posts,
            "count": len(posts)
        }
    except Exception as e:
        logger.error(f"Error getting posts by date range: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sentiment-over-time")
async def get_sentiment_over_time(days: int = Query(7, ge=1, le=30)):
    """Get sentiment trends over time."""
    try:
        return {
            "days": days,
            "data": db_service.get_sentiment_over_time(days)
        }
    except Exception as e:
        logger.error(f"Error getting sentiment over time: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Scraping Control Endpoints
# ============================================================

@app.post("/api/scrape")
async def trigger_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Trigger a scraping run."""
    try:
        if not request.force and not scraper.should_scrape():
            return {
                "status": "skipped",
                "message": "Scrape interval has not elapsed. Use force=true to override.",
                "last_scrape": scraper.get_stats().get("last_scrape_time")
            }

        # Run scraping in background
        background_tasks.add_task(_run_scrape_and_process)
        
        return {
            "status": "started",
            "message": "Scraping has been initiated in the background.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error triggering scrape: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _run_scrape_and_process():
    """Background task to run full scrape and process pipeline."""
    try:
        logger.info("Starting background scraping...")
        raw_posts = scraper.scrape_all()
        
        if raw_posts:
            stats = pipeline.process_and_save(raw_posts)
            logger.info(f"Scraping complete. Stats: {stats}")
        else:
            logger.info("No new posts collected.")
    except Exception as e:
        logger.error(f"Background scraping failed: {e}")


@app.get("/api/scrape-status")
async def get_scrape_status():
    """Get current scraping status and statistics."""
    return scraper.get_stats()


# ============================================================
# Database Management Endpoints
# ============================================================

@app.get("/api/db/stats")
async def get_db_stats():
    """Get database statistics."""
    return db_service.get_database_stats()


@app.get("/api/db/drink-stats")
async def get_drink_stats():
    """Get aggregated drink type statistics."""
    return db_service.get_drink_type_stats()


@app.post("/api/db/cleanup")
async def cleanup_old_data(days: int = Query(90, ge=1, le=365)):
    """Clean up old posts from the database."""
    try:
        deleted = db_service.cleanup_old_posts(days)
        return {
            "deleted": deleted,
            "days_kept": days
        }
    except Exception as e:
        logger.error(f"Error cleaning up: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Health Check
# ============================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "database": "connected",
            "scraper": "ready",
            "processor": "ready",
            "analytics": "ready"
        }
    }


# ============================================================
# Keywords Reference
# ============================================================

@app.get("/api/keywords")
async def get_keywords():
    """Get the list of tracked coffee keywords."""
    return {
        "keywords": COFFEE_KEYWORDS,
        "count": len(COFFEE_KEYWORDS)
    }


# ============================================================
# Run the server
# ============================================================

if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DASHBOARD_PORT,
        reload=DEBUG_MODE
    )
