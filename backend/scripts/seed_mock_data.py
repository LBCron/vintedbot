#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.db import create_tables, get_db_session
from backend.models import (
    User, Session, MessageThread, Message, PublishJob, Listing,
    JobStatus, JobMode, ListingStatus
)
from backend.utils.crypto import encrypt_blob
from backend.utils.logger import logger

def seed_data():
    """Seed database with realistic mock data"""
    
    logger.info("🌱 Seeding database with mock data...")
    
    # Ensure tables exist
    create_tables()
    
    with get_db_session() as db:
        # Create users
        user1 = User(email="test@example.com")
        db.add(user1)
        db.commit()
        db.refresh(user1)
        
        # Create sessions
        mock_cookie = "mock_session_cookie_12345"
        encrypted = encrypt_blob(mock_cookie)
        
        session1 = Session(
            user_id=user1.id,
            encrypted_cookie=encrypted,
            note="Test session for development",
            last_validated_at=datetime.utcnow()
        )
        db.add(session1)
        db.commit()
        db.refresh(session1)
        
        # Create message threads
        threads_data = [
            {
                "thread_id": "thread_001",
                "participants": {"buyer": "john_doe", "seller": "me"},
                "snippet": "Hi! Is this jacket still available?",
                "unread_count": 2,
                "last_message_at": datetime.utcnow() - timedelta(hours=2)
            },
            {
                "thread_id": "thread_002",
                "participants": {"buyer": "jane_smith", "seller": "me"},
                "snippet": "Thanks for the quick delivery!",
                "unread_count": 0,
                "last_message_at": datetime.utcnow() - timedelta(days=1)
            },
            {
                "thread_id": "thread_003",
                "participants": {"buyer": "mike_wilson", "seller": "me"},
                "snippet": "Can you ship to Germany?",
                "unread_count": 1,
                "last_message_at": datetime.utcnow() - timedelta(hours=5)
            }
        ]
        
        for thread_data in threads_data:
            thread = MessageThread(**thread_data)
            db.add(thread)
        
        db.commit()
        
        # Create messages
        messages_data = [
            {"thread_id": "thread_001", "sender": "john_doe", "body": "Hi! Is this jacket still available?"},
            {"thread_id": "thread_001", "sender": "me", "body": "Yes, it's still available! Would you like to buy it?"},
            {"thread_id": "thread_002", "sender": "jane_smith", "body": "I received the item. It's perfect!"},
            {"thread_id": "thread_002", "sender": "jane_smith", "body": "Thanks for the quick delivery!"},
            {"thread_id": "thread_002", "sender": "me", "body": "Glad you like it! Enjoy!"},
            {"thread_id": "thread_003", "sender": "mike_wilson", "body": "Can you ship to Germany?"},
        ]
        
        for msg_data in messages_data:
            message = Message(**msg_data, is_read=(msg_data["sender"] == "me"))
            db.add(message)
        
        db.commit()
        
        # Create listings
        listings_data = [
            {
                "title": "Vintage Levi's 501 Jeans",
                "description": "Classic vintage Levi's 501 jeans in excellent condition. Size 32/32. No visible wear or damage.",
                "brand": "Levi's",
                "price": 45.00,
                "status": ListingStatus.listed,
                "photos": ["https://example.com/jeans1.jpg", "https://example.com/jeans2.jpg"]
            },
            {
                "title": "Nike Air Max 90 Sneakers",
                "description": "Nike Air Max 90 sneakers, size 10. Worn only a few times, like new condition.",
                "brand": "Nike",
                "price": 80.00,
                "status": ListingStatus.listed,
                "photos": ["https://example.com/nike1.jpg"]
            },
            {
                "title": "Zara Wool Coat",
                "description": "Beautiful wool coat from Zara. Size M. Perfect for winter.",
                "brand": "Zara",
                "price": 35.00,
                "status": ListingStatus.draft,
                "photos": []
            },
            {
                "title": "Adidas Track Jacket",
                "description": "Retro Adidas track jacket. Size L. Great condition.",
                "brand": "Adidas",
                "price": 25.00,
                "status": ListingStatus.sold,
                "photos": ["https://example.com/adidas1.jpg"]
            }
        ]
        
        for listing_data in listings_data:
            listing = Listing(**listing_data)
            db.add(listing)
        
        db.commit()
        
        # Create publish jobs
        import uuid
        jobs_data = [
            {
                "job_id": str(uuid.uuid4()),
                "item_id": 1,
                "session_id": session1.id,
                "mode": JobMode.manual,
                "status": JobStatus.queued
            },
            {
                "job_id": str(uuid.uuid4()),
                "item_id": 2,
                "session_id": session1.id,
                "mode": JobMode.automated,
                "status": JobStatus.completed,
                "logs": [
                    {"timestamp": datetime.utcnow().isoformat(), "message": "Job started"},
                    {"timestamp": datetime.utcnow().isoformat(), "message": "Item published successfully"}
                ]
            }
        ]
        
        for job_data in jobs_data:
            job = PublishJob(**job_data)
            db.add(job)
        
        db.commit()
        
        logger.info("✅ Mock data seeded successfully!")
        logger.info(f"   - {len(threads_data)} message threads")
        logger.info(f"   - {len(messages_data)} messages")
        logger.info(f"   - {len(listings_data)} listings")
        logger.info(f"   - {len(jobs_data)} publish jobs")
        logger.info(f"   - 1 test session (ID: {session1.id})")


if __name__ == "__main__":
    seed_data()
