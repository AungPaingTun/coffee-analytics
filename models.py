"""
Database models for the Coffee Analytics Platform.
Defines SQLAlchemy ORM models for storing scraped social media data.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime,
    Boolean, create_engine, event
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
from config import DATABASE_URL

Base = declarative_base()


class SocialPost(Base):
    """Stores individual social media posts mentioning coffee."""
    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False, index=True)  # reddit, twitter, instagram
    post_id = Column(String(200), unique=True, nullable=False)  # unique ID from source
    platform_url = Column(Text, nullable=True)
    author = Column(String(200), nullable=True)  # anonymized username
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Extracted data
    drink_types = Column(Text, nullable=True)  # JSON list of detected drink types
    sentiment = Column(String(20), default="neutral")  # positive, neutral, negative
    sentiment_score = Column(Float, default=0.0)
    
    # Engagement metrics
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    
    # Derived analytics
    hour_of_day = Column(Integer, nullable=True)
    day_of_week = Column(Integer, nullable=True)  # 0=Monday, 6=Sunday
    engagement_score = Column(Float, default=0.0)
    estimated_age_group = Column(String(50), nullable=True)  # "18-24", "25-34", etc.
    
    # Metadata
    keywords_found = Column(Text, nullable=True)  # JSON list of matched keywords
    scraped_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)


class DailyInsight(Base):
    """Stores pre-computed daily analytics insights."""
    __tablename__ = "daily_insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(20), unique=True, nullable=False)  # YYYY-MM-DD
    total_posts = Column(Integer, default=0)
    avg_sentiment = Column(Float, default=0.0)
    positive_ratio = Column(Float, default=0.0)
    neutral_ratio = Column(Float, default=0.0)
    negative_ratio = Column(Float, default=0.0)
    top_drink_types = Column(Text, nullable=True)  # JSON
    peak_hour = Column(Integer, nullable=True)
    total_engagement = Column(Integer, default=0)
    computed_at = Column(DateTime, default=func.now())


class TrendingKeyword(Base):
    """Stores trending keywords and their frequency over time."""
    __tablename__ = "trending_keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(100), nullable=False, index=True)
    frequency = Column(Integer, default=0)
    date = Column(String(20), nullable=False)
    sentiment_avg = Column(Float, default=0.0)


# Database engine setup
engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


def get_session():
    """Get a new database session."""
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


# Event listener to enable WAL mode for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
