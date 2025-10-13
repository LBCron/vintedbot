from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlmodel import SQLModel, Field, JSON, Column
from sqlalchemy import Text


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    blocked = "blocked"
    cancelled = "cancelled"


class JobMode(str, Enum):
    manual = "manual"
    automated = "automated"


class ListingStatus(str, Enum):
    draft = "draft"
    listed = "listed"
    sold = "sold"
    archived = "archived"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    encrypted_cookie: str = Field(sa_column=Column(Text))
    note: Optional[str] = None
    last_validated_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MessageThread(SQLModel, table=True):
    __tablename__ = "message_thread"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    thread_id: str = Field(unique=True, index=True)
    participants: dict = Field(default={}, sa_column=Column(JSON))
    snippet: Optional[str] = None
    unread_count: int = Field(default=0)
    last_message_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    thread_id: str = Field(foreign_key="message_thread.thread_id", index=True)
    sender: str
    body: str = Field(sa_column=Column(Text))
    attachments: List[str] = Field(default=[], sa_column=Column(JSON))
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PublishJob(SQLModel, table=True):
    __tablename__ = "publish_job"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(unique=True, index=True)
    item_id: Optional[int] = None
    session_id: Optional[int] = Field(default=None, foreign_key="session.id")
    mode: JobMode = Field(default=JobMode.manual)
    schedule_at: Optional[datetime] = None
    status: JobStatus = Field(default=JobStatus.queued)
    logs: List[dict] = Field(default=[], sa_column=Column(JSON))
    screenshot_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Listing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str = Field(sa_column=Column(Text))
    brand: Optional[str] = None
    price: float
    status: ListingStatus = Field(default=ListingStatus.draft)
    photos: List[str] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Media(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    sha256: str = Field(max_length=64, index=True)
    filename: str = Field(max_length=255)
    mime: str = Field(max_length=64)
    width: int
    height: int
    size_bytes: int
    storage: str = Field(max_length=16)
    url: str = Field(max_length=512)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Draft(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    title: str = Field(default="", max_length=160)
    description: str = Field(default="", sa_column=Column(Text))
    price_suggested: Optional[float] = None
    status: str = Field(default="draft", max_length=24)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DraftPhoto(SQLModel, table=True):
    __tablename__ = "draft_photo"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    draft_id: int = Field(foreign_key="draft.id")
    media_id: int = Field(foreign_key="media.id")
    order_index: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
