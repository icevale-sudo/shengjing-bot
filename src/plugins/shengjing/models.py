from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot import logger, get_driver
from pathlib import Path

from src.plugins.shengjing import QrSj
from src.plugins.shengjing.config import *
from src.plugins.shengjing.hook import get_db_conn, get_db_cursor

import sqlite3
import subprocess
import os
import random


async def insert_img_quotation(image_id: int):
    conn = await get_db_conn()
    cursor = await get_db_cursor()
    sql_cmd = "INSERT INTO quotations (id, quotation, is_img) VALUES (?, '', 1)"
    await cursor.execute(sql_cmd, (image_id,))
    await conn.commit()

    logger.success(f"Tried adding image quotation, whose id is {image_id}")


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


async def get_img_path_by_id(id: str) -> str:
    file_path = f"{IMG_DIR_PATH}{id}.png"
    file_url = Path(file_path).as_uri()

    return file_url


async def get_quote_by_id(id: str) -> MessageSegment:
    cursor = await get_db_cursor()
    await cursor.execute("SELECT quotation, is_img FROM quotations WHERE id = ?", (id,))
    result = await cursor.fetchone()

    # ID is illegal
    if result is None:
        return MessageSegment.text("ERROR: No such ID in database or ID is illegal")

    if result[1] == 1:  # is image
        return MessageSegment.image(await get_img_path_by_id(id))
    else:  # is text
        return MessageSegment.text(result[0])


async def get_weighted_random_quote(weight_top_100, weight_others) -> MessageSegment:
    cursor = await get_db_cursor()

    # Get item count from database
    sql_cmd = "SELECT COUNT(*) FROM quotations"
    await cursor.execute(sql_cmd)
    item_count = (await cursor.fetchone())[0]

    # Get weighted random int
    # Rule: weights of resent 100 quotes are 0.8, while others are 0.2
    elements = [i for i in range(1, item_count + 1)]
    weights = [weight_others] * (item_count - 100) + [weight_top_100] * 100
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

    if is_img == 1:
        # If `is_img` is 1, return a Message containing image
        file_url = await get_img_path_by_id(quote_id)
        return MessageSegment.image(file_url) + MessageSegment.text(
            f"ID: {quote_id}, Position: {weighted_random_index}, Weight: {weight_top_100 if item_count - weighted_random_index <= 100 else weight_others}"
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


async def insertImgData(sj: QrSj):
    """
    Description: 将QrSj对象插入数据库
    Args:
        sj: QrSj对象

    Returns: None

    """
    conn = await get_db_conn()
    cursor = await get_db_cursor()

    # 获取当前群组的最大group_id
    sql_cmd = "SELECT MAX(group_id) FROM sj where belong_group = :belong_group and is_deleted = 1;"
    await cursor.execute(sql_cmd, {'belong_group': sj.belong_group})
    max_id_row = await cursor.fetchone()
    max_id = max_id_row[0] if max_id_row[0] is not None else 0
    print(max_id)
    sj.group_id = max_id + 1

    # 插入数据
    sql_text = "insert into sj ( img_name, img_note,  url_get, url_delete, upload_by, upload_time,belong_group,group_id) values ( :img_name, :img_note,  :url_get, :url_delete, :upload_by, :upload_time,:belong_group,:group_id);"
    await cursor.execute(sql_text, {'img_name': sj.img_name, 'img_note': sj.img_note, 'url_get': sj.url_get,
                                    'url_delete': sj.url_delete, 'upload_by': sj.upload_by,
                                    'upload_time': sj.upload_time,
                                    'belong_group': sj.belong_group, 'group_id': sj.group_id})
    await conn.commit()
    # await conn.close()
    logger.success(f"Tried adding image quotation, whose id is {sj.group_id}")


async def getRandomSj(belong_group):
    """
    Description: 随机获取一张圣经
    Args:
        belong_group: 群组号

    Returns: 圣经消息段

    """
    cursor = await get_db_cursor()
    sql_text = "select url_get,group_id,img_note from sj where belong_group = :belong_group and is_deleted = 1 order by random();"
    await cursor.execute(sql_text, {'belong_group': belong_group})
    result = await cursor.fetchone()
    return MessageSegment.image(result[0]) + MessageSegment.text(
        f"ID: {result[1]}{',标签:#' + result[2] if result[2] != '' else ''}"
    )


async def getSjById(group_id, belong_group):
    """
    Description: 根据ID获取圣经
    Args:
        group_id: 当前群组查询的ID
        belong_group: 所属群组

    Returns: 圣经消息段

    """
    cursor = await get_db_cursor()
    sql_text = "select url_get,img_note from sj where group_id = :group_id and belong_group = :belong_group;"
    await cursor.execute(sql_text, {'group_id': group_id, 'belong_group': belong_group})
    result = await cursor.fetchone()
    if result is None:
        return MessageSegment.text("未找到该圣经")
    return MessageSegment.image(result[0]) + MessageSegment.text(
        f"ID: {group_id}{',标签:#' + result[1] if result[1] != '' else ''}"
    )


async def getSjByNote(note, belong_group):
    """
    Description: 根据标签获取圣经
    Args:
        note: 标签，模糊匹配
        belong_group: 所属群组

    Returns: 圣经消息段

    """
    cursor = await get_db_cursor()
    sql_text = "select url_get,group_id,img_note from sj where img_note like :note and belong_group = :belong_group order by random();"
    await cursor.execute(sql_text, {'note': "%" + note + "%", 'belong_group': belong_group})
    result = await cursor.fetchone()
    if result is None:
        return MessageSegment.text("未找到标签的圣经")
    return MessageSegment.image(result[0]) + MessageSegment.text(
        f"ID: {result[1]}{',标签:#' + result[2]}"
    )


if __name__ == "__main__":
    pass
