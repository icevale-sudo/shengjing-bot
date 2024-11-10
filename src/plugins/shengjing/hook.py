from nonebot import get_driver
from src.plugins.shengjing.config import *

import aiosqlite

driver = get_driver()
db_conn = None


@driver.on_startup
async def connect_db():
    global db_conn
    db_conn = await aiosqlite.connect(DB_PATH)


@driver.on_shutdown
async def close_db():
    if db_conn:
        await db_conn.close()


async def get_db_conn():
    return db_conn


async def get_db_cursor():
    return await db_conn.cursor()
