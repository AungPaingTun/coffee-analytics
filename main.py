"""
Coffee Analytics Platform - Main Entry Point
Starts the FastAPI server as a long-running process.
Data scraping runs in a background thread and never blocks the server.
"""

import os
import sys
import logging
import threading
import uvicorn

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DASHBOARD_PORT
from models import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def run_scrape():
    """Run scraping in a background thread."""
    try:
        from scraper.orchestrator import ScraperOrchestrator
        from processor.pipeline import ProcessingPipeline

        logger.info("Starting background data collection...")
        scraper = ScraperOrchestrator()
        pipeline = ProcessingPipeline()
        raw_posts = scraper.scrape_all()
        logger.info(f"Collected {len(raw_posts)} raw posts from all sources.")

        if raw_posts:
            stats = pipeline.process_and_save(raw_posts)
            logger.info(f"Processing stats: {stats}")
        else:
            logger.warning("No posts collected.")
    except Exception as e:
        logger.error(f"Background scrape failed: {e}")


def start_background_scrape():
    """Start scraping in a daemon thread (won't block server shutdown)."""
    thread = threading.Thread(target=run_scrape, daemon=True)
    thread.start()


# Initialize database
init_db()

# Import the FastAPI app
from api.app import app

# Register startup event for background scraping
@app.on_event("startup")
async def start_scraping_thread():
    """Start scraping in a background thread after server is ready."""
    start_background_scrape()


# Run uvicorn as the main process — this keeps running until killed
if __name__ == "__main__":
    port = int(os.getenv("PORT", DASHBOARD_PORT))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False, log_level="info")
