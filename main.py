"""
Coffee Analytics Platform - Main Entry Point
Initializes the database and starts the FastAPI server with the dashboard.
Data scraping is triggered on-demand via the /api/scrape endpoint.
"""

import os
import sys
import logging
import uvicorn

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DASHBOARD_PORT, DEBUG_MODE
from models import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the Coffee Analytics Platform."""
    print("=" * 60)
    print("  Coffee Analytics Platform v1.0")
    print("  Social Media Data Scraper & Analytics Dashboard")
    print("=" * 60)

    # Step 1: Initialize database
    logger.info("Initializing database...")
    init_db()
    logger.info("Database ready.")

    # Step 2: Determine port (Railway injects PORT env var)
    port = int(os.getenv("PORT", DASHBOARD_PORT))
    logger.info(f"Starting server on port {port}...")

    print(f"\n  Dashboard available at: http://localhost:{port}")
    print(f"  API docs available at:  http://localhost:{port}/docs")
    print(f"  Scraping via:           POST http://localhost:{port}/api/scrape")
    print(f"\n{'=' * 60}\n")

    # Step 3: Start uvicorn server
    # Scraping is triggered on-demand via POST /api/scrape
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
