import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from backend.db import (
    get_threads, get_messages, save_message, mark_messages_read,
    queue_publish_job, get_db_session
)
from backend.models import MessageThread
from backend.utils.validators import is_valid_file_extension, validate_file_size, sanitize_filename
from backend.utils.logger import logger

router = APIRouter(prefix="/vinted/messages", tags=["messages"])


class ReplyRequest(BaseModel):
    session_id: int
    text: str
    send_mode: str = "manual"


class BulkMarkReadRequest(BaseModel):
    thread_ids: List[str]


@router.get("")
async def get_message_threads(
    since: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get paginated message threads"""
    threads = get_threads(limit=limit, offset=offset)
    
    return {
        "threads": [
            {
                "thread_id": t.thread_id,
                "participants": t.participants,
                "snippet": t.snippet,
                "unread_count": t.unread_count,
                "last_message_at": t.last_message_at,
                "created_at": t.created_at
            }
            for t in threads
        ],
        "total": len(threads),
        "limit": limit,
        "offset": offset
    }


@router.get("/notifications")
async def get_notifications():
    """Get unread message counts"""
    threads = get_threads(limit=1000)
    
    total_unread = sum(t.unread_count for t in threads)
    unread_threads = [t for t in threads if t.unread_count > 0]
    
    return {
        "total_unread": total_unread,
        "unread_threads_count": len(unread_threads),
        "threads": [
            {
                "thread_id": t.thread_id,
                "unread_count": t.unread_count,
                "snippet": t.snippet
            }
            for t in unread_threads[:10]
        ]
    }


@router.get("/{thread_id}")
async def get_thread_messages(
    thread_id: str,
    limit: int = 50,
    offset: int = 0
):
    """Get messages for a specific thread"""
    messages = get_messages(thread_id, limit=limit, offset=offset)
    
    return {
        "messages": [
            {
                "id": m.id,
                "thread_id": m.thread_id,
                "sender": m.sender,
                "body": m.body,
                "attachments": m.attachments,
                "is_read": m.is_read,
                "created_at": m.created_at
            }
            for m in messages
        ],
        "total": len(messages)
    }


@router.post("/{thread_id}/reply")
async def reply_to_thread(thread_id: str, data: ReplyRequest):
    """Reply to a message thread"""
    
    if data.send_mode == "manual":
        # Create a draft/preview job
        job = queue_publish_job(
            item_id=None,
            session_id=data.session_id,
            mode="manual"
        )
        
        # Save message as draft
        message = save_message(
            thread_id=thread_id,
            sender="me",
            body=data.text
        )
        
        logger.info(f"📝 Draft reply created for thread {thread_id}")
        
        return {
            "job_id": job.job_id,
            "preview_url": f"/preview/{job.job_id}",
            "message_id": message.id
        }
    
    elif data.send_mode == "automated":
        # Queue automated send job
        job = queue_publish_job(
            item_id=None,
            session_id=data.session_id,
            mode="automated"
        )
        
        logger.info(f"🤖 Automated reply queued for thread {thread_id}")
        
        return {
            "job_id": job.job_id,
            "status": "queued"
        }
    
    else:
        raise HTTPException(status_code=400, detail="Invalid send_mode")


@router.post("/send-attachment")
async def send_attachment(
    file: UploadFile = File(...),
    thread_id: str = Form(...)
):
    """Upload an attachment for a message"""
    
    # Validate file
    if not is_valid_file_extension(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Read file
    contents = await file.read()
    
    if not validate_file_size(len(contents)):
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Save file
    filename = sanitize_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    filepath = f"backend/data/uploads/{unique_filename}"
    
    with open(filepath, "wb") as f:
        f.write(contents)
    
    file_url = f"/uploads/{unique_filename}"
    
    logger.info(f"📎 Attachment uploaded: {file_url}")
    
    return {
        "success": True,
        "url": file_url,
        "filename": filename
    }


@router.post("/bulk-mark-read")
async def bulk_mark_read(data: BulkMarkReadRequest):
    """Mark multiple threads as read"""
    for thread_id in data.thread_ids:
        mark_messages_read(thread_id)
    
    logger.info(f"✅ Marked {len(data.thread_ids)} threads as read")
    
    return {
        "success": True,
        "marked_count": len(data.thread_ids)
    }
