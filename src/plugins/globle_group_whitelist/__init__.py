from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.message import event_preprocessor
from nonebot.exception import IgnoredException
from nonebot import get_driver


# Read config
config = get_driver().config
GROUP_WHITELIST = set(config.group_whitelist)


#Block messages not in GROUP_WHITELIST
@event_preprocessor
async def group_whitelist_filter(event: GroupMessageEvent):
    if event.group_id not in GROUP_WHITELIST:
        raise IgnoredException("Message is not from whitelisted groups")