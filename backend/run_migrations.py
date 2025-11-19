#!/usr/bin/env python3
"""
Database Migration Runner
Executes SQL migrations for VintedBot database

SECURITY: Uses parameterized queries and environment variables
"""
import os
import sys
import asyncio
import asyncpg
from pathlib import Path
from loguru import logger


async def run_migrations():
    """
    Run all pending database migrations
    """
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    # Get migrations directory
    migrations_dir = Path(__file__).parent / "migrations"
    
    if not migrations_dir.exists():
        logger.error(f"Migrations directory not found: {migrations_dir}")
        return False
    
    # Find all migration files
    migration_files = sorted([
        f for f in migrations_dir.glob("*.sql")
        if not f.name.startswith("002_rollback")  # Skip rollback scripts
    ])
    
    if not migration_files:
        logger.info("No migrations found")
        return True
    
    logger.info(f"Found {len(migration_files)} migration(s)")
    
    try:
        # Connect to database
        logger.info("Connecting to database...")
        conn = await asyncpg.connect(database_url)
        
        # Create migrations tracking table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) UNIQUE NOT NULL,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check which migrations have already been run
        executed = await conn.fetch("""
            SELECT filename FROM schema_migrations
        """)
        
        executed_filenames = {row["filename"] for row in executed}
        
        # Run pending migrations
        for migration_file in migration_files:
            filename = migration_file.name
            
            if filename in executed_filenames:
                logger.info(f"⏭️  Skipping {filename} (already executed)")
                continue
            
            logger.info(f"🔄 Running migration: {filename}")
            
            # Read migration SQL
            sql = migration_file.read_text()
            
            # Execute migration
            try:
                await conn.execute(sql)
                
                # Record as executed
                await conn.execute("""
                    INSERT INTO schema_migrations (filename)
                    VALUES ($1)
                """, filename)
                
                logger.info(f"✅ Migration completed: {filename}")
                
            except Exception as e:
                logger.error(f"❌ Migration failed: {filename}")
                logger.error(f"Error: {e}")
                await conn.close()
                return False
        
        await conn.close()
        logger.info("✅ All migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_migrations())
    sys.exit(0 if success else 1)
