from typing import Any, Coroutine

from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot import logger, get_driver, get_bot
from pathlib import Path

from src.plugins.shengjing.config import *
from src.plugins.shengjing.hook import get_db_conn, get_db_cursor

import subprocess
import os
import random
import time
import base64


async def insert_img_quotation(image_id: int):
    conn = await get_db_conn()
    cursor = await get_db_cursor()
    sql_cmd = "INSERT INTO quotations (id, quotation, is_img) VALUES (?, '', 1)"
    await cursor.execute(sql_cmd, (image_id,))
    await conn.commit()

    logger.success(f"Tried adding image quotation, whose id is {image_id}")


async def insert_quote_blame(quote_id: int, created_timestamp: int, requester_id: str, sender_id: str):
    conn = await get_db_conn()
    cursor = await get_db_cursor()
    sql_cmd = "INSERT INTO blames (id, createdTime, requester, sender) VALUES (?, ?, ?, ?)"
    timestring = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_timestamp))
    await cursor.execute(sql_cmd, (quote_id, timestring, requester_id, sender_id))
    await conn.commit()

    logger.success(
        f"Tried adding quotation blame, id: {quote_id}, time: {timestring}, req: {requester_id}, sender: {sender_id}")


async def get_quote_blame(quote_id: int):
    cursor = await get_db_cursor()
    # Query to check if the row exists and fetch the victim data
    await cursor.execute(f"SELECT createdTime, requester, sender FROM blames WHERE id = ?", (quote_id,))
    row = await cursor.fetchone()

    # If the victims exists, parse the JSON data and return the list of strings
    if row:
        createdTime, requester_id, sender_id = row
        return createdTime, requester_id, sender_id
    else:
        return None


async def insert_quote_victim(quote_id: int, victim: str):
    conn = await get_db_conn()
    cursor = await get_db_cursor()
    # Check if the victim exist to avoid duplication
    await cursor.execute(f"SELECT victim FROM victims WHERE quote_id = ? AND victim = ?", (quote_id, victim))
    result = await cursor.fetchone()

    if not result:
        sql_cmd = "INSERT INTO victims (quote_id, victim) VALUES (?, ?)"
        await cursor.execute(sql_cmd, (quote_id, victim))
        await conn.commit()

        logger.success(f"Tried adding quotation victim, id: {quote_id}, victims: {victim}")


async def get_quote_victim(quote_id: int):
    cursor = await get_db_cursor()
    # Query to check if the row exists and fetch the victim data
    await cursor.execute(f"SELECT victim FROM victims WHERE quote_id = ?", (quote_id,))
    victims = await cursor.fetchall()

    # If the victims exists, parse the JSON data and return the list of strings
    if len(victims) > 0:
        return [u[0] for u in victims]
    else:
        return None


async def remove_quote_victim(quote_id: int, victim: str):
    conn = await get_db_conn()
    cursor = await get_db_cursor()
    if await is_quote_exist_in_db(quote_id):
        await cursor.execute("DELETE FROM victims WHERE quote_id=? AND victim=?", (quote_id, victim))
        await conn.commit()
        logger.success(f"Remove victim {victim} from quotation {quote_id}")


async def remove_quote_all_victims(quote_id: int):
    conn = await get_db_conn()
    cursor = await get_db_cursor()
    if await is_quote_exist_in_db(quote_id):
        await cursor.execute("DELETE FROM victims WHERE quote_id=?", (quote_id,))
        await conn.commit()
        logger.success(f"Remove all victims from quotation {quote_id}")


async def get_max_id() -> int:
    cursor = await get_db_cursor()
    sql_cmd = "SELECT MAX(id) FROM quotations"
    await cursor.execute(sql_cmd)
    max_id_row = await cursor.fetchone()

    # Return 0 when there is no item in db
    max_id = max_id_row[0] if max_id_row[0] is not None else 0

    return max_id


def extract_image_urls(message: MessageSegment) -> list:
    image_urls = [seg.data["url"] for seg in message if seg.type == "image"]

    return image_urls


async def download_image(url: str):
    filename = os.path.join(IMG_DIR_PATH, f"{await get_max_id() + 1}.png")
    command = ["curl", "-o", filename, url]
    subprocess.run(command, capture_output=True, text=True)


async def get_img_base64_uri_by_id(id: str) -> str:
    file_path = Path(f"{IMG_DIR_PATH}{id}.png")
    with open(file_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode()
    img_base64_uri = f"base64://{img_base64}"

    return img_base64_uri


async def get_name_str_by_user_id(user_id: str):
    bot = get_bot()
    result = await bot.get_stranger_info(user_id=int(user_id))
    if result:
        return f"{result.get('nickname')}({user_id})"
    else:
        return user_id


async def get_quote_blame_victim_str_by_id(id: str) -> str:
    # Get blame info if exist
    blames = await get_quote_blame(id)
    blame_str = ''
    if not blames is None:
        createdTime, requester_id, sender_id = blames
        requester_str = await get_name_str_by_user_id(requester_id)
        blame_str = f'\n添加时间: {createdTime}'
        blame_str += f'\n添加者: {requester_str}'
        if requester_id != sender_id:
            sender_str = await get_name_str_by_user_id(sender_id)
            blame_str += f'\n发送者: {sender_str}'

    # Get victim info if exist
    victims = await get_quote_victim(id)
    victims_str = ''
    if victims is None:
        victims_str = f'\n正主: 待添加'
    elif len(victims) == 1:
        victim = victims[0]
        victim_str = await get_name_str_by_user_id(victim)
        victims_str = f'\n正主: {victim_str}'
    else:
        victims_str = f'\n正主:'
        for u in victims:
            victims_str += '\n' + await get_name_str_by_user_id(u)

    return blame_str + victims_str


async def get_quote_by_id(id: str):
    cursor = await get_db_cursor()
    await cursor.execute("SELECT quotation, is_img FROM quotations WHERE id = ?", (id,))
    result = await cursor.fetchone()

    # ID is illegal
    if result is None:
        return MessageSegment.text("ERROR: No such ID in database or ID is illegal")

    bvstr = await get_quote_blame_victim_str_by_id(id)

    if result[1] == 1:  # is image
        return MessageSegment.image(await get_img_base64_uri_by_id(id)) + MessageSegment.text(bvstr)
    else:  # is text
        return MessageSegment.text(result[0] + '\n' + bvstr)


async def get_weighted_random_quote(weight_top_100, weight_others):
    cursor = await get_db_cursor()

    # Get item count from database
    sql_cmd = "SELECT COUNT(*) FROM quotations"
    await cursor.execute(sql_cmd)
    item_count = (await cursor.fetchone())[0]

    # Get weighted random int
    # Rule: weights of resent 100 quotes are 0.8, while others are 0.2
    elements = [i for i in range(1, item_count + 1)]
    if item_count > 100:
        weights = [weight_others] * (item_count - 100) + [weight_top_100] * 100
    else:
        weights = [weight_top_100] * item_count
    weighted_random_index = random.choices(elements, weights)[0]

    # Get quote id
    sql_cmd = "SELECT id FROM quotations ORDER BY id LIMIT 1 OFFSET ?"
    await cursor.execute(sql_cmd, (weighted_random_index - 1,))
    quote_id = (await cursor.fetchone())[0]

    # Get details of the quote
    sql_cmd = "SELECT quotation, is_img FROM quotations WHERE id = ?"
    await cursor.execute(sql_cmd, (quote_id,))
    result = await cursor.fetchone()

    quote, is_img = result
    selection_str = f"ID: {quote_id}, Position: {weighted_random_index}"
    bvstr = await get_quote_blame_victim_str_by_id(quote_id)

    if is_img == 1:
        # If `is_img` is 1, return a Message containing image
        file_base64_uri = await get_img_base64_uri_by_id(quote_id)
        return MessageSegment.image(file_base64_uri) + MessageSegment.text(
            selection_str + bvstr
        )
    else:
        return MessageSegment.text(f"{quote}\n\n ID: {quote_id}")


async def get_call_count(call_type: str):
    """Get call times with a specific call type.

    Args:
        call_type (str): Possible values include:
            - "all": Sum following types up.
            - "get_random"
            - "get_by_id"
            - "add_image"
            - "get_max_id"
    """
    possible_value_list = [
        "all",
        "get_random",
        "get_by_id",
        "add_image",
        "get_max_id",
    ]
    if call_type not in possible_value_list:
        raise ValueError(
            f"Invalid call_type '{call_type}'. Must be one of {possible_value_list}"
        )

    cursor = await get_db_cursor()

    # Count all
    if call_type == "all":
        await cursor.execute("SELECT SUM(count) FROM call_counts")
        result = (await cursor.fetchone())[0]
    else:  # Select call count of the specific call_type
        await cursor.execute(
            "SELECT count FROM call_counts WHERE call_type = ?", (call_type,)
        )
        try:
            result = (await cursor.fetchone())[0]
        except TypeError:  # If call_type is not in database
            result = None

    return result


async def record_call_count(call_type: str):
    """Record call times with a specific call type.

    Args:
        call_type (str): Possible values include:
            - "get_random"
            - "get_by_id"
            - "add_image"
            - "get_max_id"

    Raises:
        ValueError: If call_type is not one of the possible values.
    """
    possible_value_list = [
        "get_random",
        "get_by_id",
        "add_image",
        "get_max_id",
    ]
    if call_type not in possible_value_list:
        raise ValueError(
            f"Invalid call_type '{call_type}'. Must be one of {possible_value_list}"
        )

    current_count = await get_call_count(call_type)

    conn = await get_db_conn()
    cursor = await get_db_cursor()

    if current_count:
        new_count = current_count + 1
        await cursor.execute(
            "UPDATE call_counts SET count = ? WHERE call_type = ?",
            (new_count, call_type),
        )
    else:
        await cursor.execute(
            "INSERT INTO call_counts (call_type, count) VALUES (?, ?)", (call_type, 1)
        )

    await conn.commit()


async def remove_quote(id: str) -> MessageSegment:
    conn = await get_db_conn()
    cursor = await get_db_cursor()
    if await is_quote_exist_in_db(id):
        await cursor.execute("DELETE FROM quotations WHERE id=?", (id,))
        await cursor.execute("DELETE FROM blames WHERE id=?", (id,))
        await cursor.execute("DELETE FROM victims WHERE quote_id=?", (id,))
        await conn.commit()

        # Remove from img directory
        command = ["mv", f"{IMG_DIR_PATH}{id}.png", f"{IMG_DIR_PATH}trash/"]
        subprocess.run(command)

        return MessageSegment.text(f"成功删除圣经{id}")
    else:
        return MessageSegment.text("错误：数据库中无该圣经")


async def is_quote_exist_in_db(id: str) -> bool:
    cursor = await get_db_cursor()
    await cursor.execute("SELECT COUNT(*) FROM quotations WHERE id=?", (id,))
    count = (await cursor.fetchone())[0]
    if count > 0:
        return True
    else:
        return False


if __name__ == "__main__":
    pass
