from nonebot import logger, get_driver
from src.plugins.shengjing.config import *

import aiosqlite
from pathlib import Path

driver = get_driver()
db_conn = None


@driver.on_startup
async def connect_db():
    global db_conn
    db_conn = await aiosqlite.connect(DB_PATH)
    await initialize_db()


@driver.on_shutdown
async def close_db():
    if db_conn:
        await db_conn.close()


async def get_db_conn():
    return db_conn


async def get_db_cursor():
    return await db_conn.cursor()

async def initialize_db():
    """
    Check if the database is correctly initialized and initialize it if it's not.
    """
    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = await get_db_conn()
    cursor = await get_db_cursor()

    # Check if the `quotations` table exists
    await cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quotations'")
    if not (await cursor.fetchone()):
        # Create the `quotations` table if it doesn't exist
        await cursor.execute("""
            CREATE TABLE quotations (
                id INTEGER PRIMARY KEY,
                quotation TEXT,
                is_img INTEGER DEFAULT 0
            )
        """)
        logger.success("Created `quotations` table.")

    # Check if the `blames` table exists
    await cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blames'")
    if not (await cursor.fetchone()):
        # Create the `quotations` table if it doesn't exist
        await cursor.execute("""
            CREATE TABLE blames (
                id INTEGER PRIMARY KEY,
                createdTime TEXT,
                requester TEXT,
                sender TEXT
            )
        """)
        logger.success("Created `blames` table.")
    
    # Check if the `victims` table exists
    await cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='victims'")
    if not (await cursor.fetchone()):
        # Create the `quotations` table if it doesn't exist
        await cursor.execute("""
            CREATE TABLE victims (
                id INTEGER PRIMARY KEY,
                quote_id INTEGER,
                victim TEXT,
                FOREIGN KEY (quote_id) REFERENCES quotations (id)
            )
        """)
        logger.success("Created `victims` table.")
    
    # Check if the `call_counts` table exists
    await cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='call_counts'")
    if not (await cursor.fetchone()):
        # Create the `call_counts` table if it doesn't exist
        await cursor.execute("""
            CREATE TABLE call_counts (
                call_type TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            )
        """)
        logger.success("Created `call_counts` table.")

    # Commit changes and close the connection
    await conn.commit()

    # Ensure the image directory exists
    img_dir = Path(IMG_DIR_PATH)
    if not img_dir.exists():
        img_dir.mkdir(parents=True, exist_ok=True)
        logger.success(f"Created image directory at {IMG_DIR_PATH}.")

    logger.success("Database initialization check complete.")
