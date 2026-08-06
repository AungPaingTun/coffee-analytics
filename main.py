"""
Coffee Analytics Platform - Main Entry Point
Initializes the application, runs the scraper, processes data,
and starts the FastAPI server with the dashboard.
"""

import os
import sys
import logging
import threading
import uvicorn

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DASHBOARD_PORT, DEBUG_MODE
from models import init_db
from processor.pipeline import ProcessingPipeline
from scraper.orchestrator import ScraperOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def run_initial_scrape():
    """Run initial data collection in a background thread."""
    try:
        logger.info("Running initial data collection...")
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
        logger.error(f"Initial scrape failed: {e}")


def main():
    """Main entry point for the Coffee Analytics Platform."""
    print("=" * 60)
    print("  ☕ Coffee Analytics Platform v1.0")
    print("  Social Media Data Scraper & Analytics Dashboard")
    print("=" * 60)

    # Step 1: Initialize database
    logger.info("Initializing database...")
    init_db()
    logger.info("Database ready.")

    # Step 2: Start the FastAPI server immediately
    print(f"\n  Dashboard available at: http://localhost:{DASHBOARD_PORT}")
    print(f"  API docs available at:  http://localhost:{DASHBOARD_PORT}/docs")
    print(f"\n{'=' * 60}\n")

    # Step 3: Run scraping in background thread
    scrape_thread = threading.Thread(target=run_initial_scrape, daemon=True)
    scrape_thread.start()

    # Step 4: Start uvicorn server
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=DASHBOARD_PORT,
        reload=DEBUG_MODE,
        log_level="info"
    )


if __name__ == "__main__":
    main()
