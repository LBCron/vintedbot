"""
Database configuration and models for VintedBot API
Uses PostgreSQL with SQLAlchemy for FastAPI
"""
import os
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

# Database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable not set")

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Models
class PhotoPlan(Base):
    """Stores photo analysis plans for bulk processing"""
    __tablename__ = "photo_plans"
    
    plan_id = Column(String(8), primary_key=True, index=True)
    photo_paths = Column(JSON, nullable=False)  # List of photo file paths
    photo_count = Column(Integer, nullable=False)
    auto_grouping = Column(Boolean, default=False)
    estimated_items = Column(Integer, nullable=False)
    detected_items = Column(Integer, nullable=True)  # REAL count from GPT-4 analysis
    draft_ids = Column(JSON, default=list)  # List of generated draft IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            "plan_id": self.plan_id,
            "photo_paths": self.photo_paths,
            "photo_count": self.photo_count,
            "auto_grouping": self.auto_grouping,
            "estimated_items": self.estimated_items,
            "detected_items": self.detected_items,
            "draft_ids": self.draft_ids if self.draft_ids is not None else [],
            "created_at": self.created_at.isoformat() if self.created_at is not None else None
        }


class BulkJob(Base):
    """Stores bulk processing job status (legacy ingest jobs)"""
    __tablename__ = "bulk_jobs"
    
    job_id = Column(String(8), primary_key=True, index=True)
    status = Column(String(20), nullable=False)  # pending, processing, completed, failed
    total_photos = Column(Integer, default=0)
    processed_photos = Column(Integer, default=0)
    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    drafts = Column(JSON, default=list)  # List of draft IDs
    errors = Column(JSON, default=list)  # List of error messages
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            "job_id": self.job_id,
            "status": self.status,
            "total_photos": self.total_photos,
            "processed_photos": self.processed_photos,
            "total_items": self.total_items,
            "completed_items": self.completed_items,
            "failed_items": self.failed_items,
            "drafts": self.drafts if self.drafts is not None else [],
            "errors": self.errors if self.errors is not None else [],
            "started_at": self.started_at.isoformat() if self.started_at is not None else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at is not None else None,
            "progress_percent": (self.completed_items / self.total_items * 100) if self.total_items > 0 else 0.0
        }


# Database initialization
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


# Dependency for FastAPI routes
def get_db():
    """FastAPI dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for database session (for non-FastAPI code)"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Helper functions
def save_photo_plan(plan_id: str, photo_paths: List[str], photo_count: int, 
                    auto_grouping: bool, estimated_items: int) -> PhotoPlan:
    """Save a photo plan to the database"""
    with get_db_context() as db:
        plan = PhotoPlan(
            plan_id=plan_id,
            photo_paths=photo_paths,
            photo_count=photo_count,
            auto_grouping=auto_grouping,
            estimated_items=estimated_items,
            created_at=datetime.utcnow()
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan


def get_photo_plan(plan_id: str) -> Optional[dict]:
    """Retrieve a photo plan from the database"""
    with get_db_context() as db:
        plan = db.query(PhotoPlan).filter(PhotoPlan.plan_id == plan_id).first()
        if plan:
            return plan.to_dict()
        return None


def update_photo_plan_results(plan_id: str, detected_items: int, draft_ids: List[str]) -> bool:
    """Update photo plan with real analysis results"""
    with get_db_context() as db:
        plan = db.query(PhotoPlan).filter(PhotoPlan.plan_id == plan_id).first()
        if plan:
            plan.detected_items = detected_items
            plan.draft_ids = draft_ids
            db.commit()
            return True
        return False


def delete_photo_plan(plan_id: str) -> bool:
    """Delete a photo plan from the database"""
    with get_db_context() as db:
        plan = db.query(PhotoPlan).filter(PhotoPlan.plan_id == plan_id).first()
        if plan:
            db.delete(plan)
            db.commit()
            return True
        return False
