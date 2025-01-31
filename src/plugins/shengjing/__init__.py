from nonebot import on_shell_command, on_fullmatch, on_regex
from nonebot.adapters.onebot.v11 import Message, Event, Bot
from nonebot.params import CommandArg, ShellCommandArgs, RegexStr
from nonebot.rule import Namespace, ArgumentParser
from nonebot.permission import SUPERUSER

from src.plugins.shengjing.models import *

import re

# Define arguments of the command
parser = ArgumentParser("sj", add_help=False)
parser.add_argument("--max-id", action="store_true")
parser.add_argument("-i", "--img", action="store_true")
parser.add_argument("-n", "--id")
parser.add_argument("-c", "--call-count", action="store_true")

shengjing = on_shell_command(
    "圣经", aliases={"sj"}, priority=5, block=True, parser=parser
)


@shengjing.handle()
async def handle_get_quote(args: Message = CommandArg()):
    """Handled when a user requests a random quote.

    Args:
        args (Message, optional): Defaults to CommandArg().
    """
    if not args.extract_plain_text():  # Message is only "sj"
        await record_call_count("get_random")

        # await shengjing.send(await get_random_quote())
        await shengjing.send(await get_weighted_random_quote(0.8, 0.2))


@shengjing.handle()
async def handle_max_id(args: Namespace = ShellCommandArgs()):
    """Handled when a user requests the maximum ID in the database.

    Args:
        args (Namespace, optional): Defaults to ShellCommandArgs().
    """
    if args.max_id:
        await record_call_count("get_max_id")
        await shengjing.send(f"当前最大ID: {await get_max_id()}")


@shengjing.handle()
async def handle_call_counts(args: Namespace = ShellCommandArgs()):
    #     if args.call_count:
    #         logger.info(args.call_count)
    #         if count := await get_call_count(args.call_count):
    #             await shengjing.send(str(count))
    #         else:
    #             await shengjing.send(
    #                 """错误: call_type 不合法
    # call_type (str): Possible values include:
    # - \"get_random\"
    # - \"get_by_id\"
    # - \"add_image\"
    # - \"get_max_id\""""
    #             )
    if args.call_count:
        await shengjing.send(str(await get_call_count("all")))


shengjing_add_img = on_fullmatch(("添加", "tj"), block=False)
shengjing_specify = on_regex(r"^(sj|圣经)\d+")
shengjing_remove = on_regex(r"^(删除)\d+", permission=SUPERUSER)


@shengjing_add_img.handle()
async def handle_func(event: Event, bot: Bot):
    """Handled when a user adds a image quote to the database.

    Args:
        event (Event): To retrieve the image specified by the user
    """
    await record_call_count("add_image")

    reply_message = (
        event.reply.message
        if hasattr(event, "reply") and event.reply
        else event.message
    )
    image_urls = extract_image_urls(reply_message)

    # Only require one image
    if len(image_urls) != 1:
        await shengjing.finish("请回复一张待添加图片")

    await download_image(image_urls[0])
    img_id = await get_max_id() + 1
    await insert_img_quotation(img_id)
    # await shengjing.send(f"添加成功, ID: {str(img_id)}")
    await bot.call_api(
        "set_msg_emoji_like", message_id=event.message_id, emoji_id="124"
    )


@shengjing_specify.handle()
async def handle_func(reg_str: str = RegexStr()):
    """Handled when a user requests the quote specified by an ID."""
    await record_call_count("get_by_id")

    id = re.search(r"\d+", reg_str)
    res = await get_quote_by_id(id.group())
    await shengjing.send(res)


@shengjing_remove.handle()
async def handle_func(reg_str: str = RegexStr()):
    id = re.search(r"\d+", reg_str)
    res = await remove_quote(id.group())
    await shengjing.send(res)
