import os
from sqlmodel import SQLModel, create_engine, Session as DBSession, select
from typing import Optional, List
from datetime import datetime
from backend.models import (
    User, Session, MessageThread, Message, PublishJob, Listing,
    JobStatus, JobMode, ListingStatus
)

# Force SQLite database (ignore Replit's PostgreSQL DATABASE_URL)
DATABASE_URL = os.getenv("VINTEDBOT_DATABASE_URL", "sqlite:///backend/data/db.sqlite")
engine = create_engine(DATABASE_URL, echo=False)


def create_tables():
    """Initialize database tables"""
    SQLModel.metadata.create_all(engine)
    print("Database tables created successfully")


def get_db_session():
    """Get database session context manager"""
    return DBSession(engine)


def get_session(session_id: int) -> Optional[Session]:
    """Get session by ID"""
    with get_db_session() as db:
        return db.get(Session, session_id)


def save_message(thread_id: str, sender: str, body: str, attachments: List[str] = None) -> Message:
    """Save a new message to a thread"""
    with get_db_session() as db:
        message = Message(
            thread_id=thread_id,
            sender=sender,
            body=body,
            attachments=attachments or []
        )
        db.add(message)
        
        # Update thread
        thread = db.exec(select(MessageThread).where(MessageThread.thread_id == thread_id)).first()
        if thread:
            thread.snippet = body[:100]
            thread.last_message_at = datetime.utcnow()
            thread.unread_count += 1
            db.add(thread)
        
        db.commit()
        db.refresh(message)
        return message


def queue_publish_job(item_id: int, session_id: int, mode: str, schedule_at: Optional[datetime] = None) -> PublishJob:
    """Create a new publish job"""
    import uuid
    with get_db_session() as db:
        job = PublishJob(
            job_id=str(uuid.uuid4()),
            item_id=item_id,
            session_id=session_id,
            mode=JobMode(mode),
            schedule_at=schedule_at,
            status=JobStatus.queued
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job


def get_publish_job(job_id: str) -> Optional[PublishJob]:
    """Get publish job by job_id"""
    with get_db_session() as db:
        return db.exec(select(PublishJob).where(PublishJob.job_id == job_id)).first()


def update_job_status(job_id: str, status: JobStatus, logs: List[dict] = None, screenshot_path: str = None):
    """Update publish job status"""
    with get_db_session() as db:
        job = db.exec(select(PublishJob).where(PublishJob.job_id == job_id)).first()
        if job:
            job.status = status
            if logs:
                job.logs = logs
            if screenshot_path:
                job.screenshot_path = screenshot_path
            job.updated_at = datetime.utcnow()
            db.add(job)
            db.commit()


def get_threads(limit: int = 50, offset: int = 0) -> List[MessageThread]:
    """Get message threads with pagination"""
    with get_db_session() as db:
        return db.exec(
            select(MessageThread)
            .order_by(MessageThread.last_message_at.desc())
            .limit(limit)
            .offset(offset)
        ).all()


def get_messages(thread_id: str, limit: int = 50, offset: int = 0) -> List[Message]:
    """Get messages for a thread"""
    with get_db_session() as db:
        return db.exec(
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        ).all()


def mark_messages_read(thread_id: str):
    """Mark all messages in a thread as read"""
    with get_db_session() as db:
        messages = db.exec(select(Message).where(Message.thread_id == thread_id)).all()
        for msg in messages:
            msg.is_read = True
            db.add(msg)
        
        # Update thread unread count
        thread = db.exec(select(MessageThread).where(MessageThread.thread_id == thread_id)).first()
        if thread:
            thread.unread_count = 0
            db.add(thread)
        
        db.commit()


def get_all_listings(limit: int = 100, offset: int = 0) -> List[Listing]:
    """Get all listings with pagination"""
    with get_db_session() as db:
        return db.exec(
            select(Listing)
            .order_by(Listing.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).all()


def get_listing(listing_id: int) -> Optional[Listing]:
    """Get listing by ID"""
    with get_db_session() as db:
        return db.get(Listing, listing_id)
