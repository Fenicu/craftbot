import re
import typing
import warnings
from ast import literal_eval
from typing import Iterable, List, Optional, Pattern, Union

from aiogram import types
from aiogram.dispatcher.filters import AdminFilter as OldAdminFilter
from aiogram.dispatcher.filters import BoundFilter, Filter
from aiogram.dispatcher.handler import ctx_data
from aiogram.types.chat_member import ChatMemberAdministrator, ChatMemberOwner
from loguru import logger

from support import models
from support.bots import dp

ChatIDArgumentType = typing.Union[typing.Iterable[typing.Union[int, str]], str, int]


def extract_chat_ids(chat_id: ChatIDArgumentType) -> typing.Set[int]:
    if isinstance(chat_id, str):
        return {int(chat_id)}
    if isinstance(chat_id, Iterable):
        return {int(item) for (item) in chat_id}
    return {chat_id}


class GlobalAdminFilter(BoundFilter):
    """
    Фильтр для проверки UserType.admin
    """

    key = "global_admin"

    def __init__(self, global_admin: bool):
        if global_admin is False:
            raise ValueError("global_admin cannot be False")

    async def check(self, update: Union[types.Message, types.CallbackQuery]):
        data = ctx_data.get()
        User: models.UserType = data["user"]
        return User.admin


class FsmFilter(BoundFilter):
    """
    Фильтр для считывания состояния пользователя
    """

    key = "my_state"

    def __init__(self, my_state: Union[str, List[str], bool]):
        if not isinstance(my_state, (str, list, bool)):
            raise ValueError(f"my_state must be str or list, not {type(my_state)}")
        elif isinstance(my_state, str):
            self.my_state = [my_state]
        else:
            self.my_state = my_state

    async def check(self, update):
        data = ctx_data.get()
        User: models.UserType = data["user"]
        if isinstance(self.my_state, bool):
            return User.fsm == str()
        return User.fsm in self.my_state


class JsonCallbackDataFilter(BoundFilter):
    """
    Фильтр сверяет ключи/значения в callback data по заданным ключам
    """

    key = "json_check"

    def __init__(self, json_check: Union[dict, str]):
        if isinstance(json_check, dict):
            self.type = type(json_check)
            self.json = json_check
        elif isinstance(json_check, str):
            self.type = type(json_check)
            self.json = json_check
        else:
            raise TypeError(f"json must be dict or str, not {type(json_check)}")

    async def check(self, call: types.CallbackQuery):
        try:
            calldata: dict = literal_eval(call.data)
            if not isinstance(calldata, dict):
                raise TypeError()
        except Exception:
            return False
        if self.type == dict:
            for key, value in self.json.items():

                if isinstance(value, type):
                    if isinstance(calldata[key], value):
                        return {"jsondata": calldata}
                    return False

                if key not in calldata:
                    return False

                if not calldata[key] == value:
                    return False

        elif self.type == str:
            if self.json not in calldata:
                return False
        return {"jsondata": calldata}


class RegexpFsmFilter(BoundFilter):
    """
    Фильтр использует регулярные выражения для поиска конечного автомата
    Принимает строку или паттерн
    """

    key = "regexp_fsm"

    def __init__(self, regexp_fsm: Union[Pattern, str]):
        if not isinstance(regexp_fsm, Pattern):
            regexp_fsm = re.compile(regexp_fsm, flags=re.IGNORECASE | re.MULTILINE)
        self.regexp_fsm = regexp_fsm

    async def check(self, obj):
        data = ctx_data.get()
        User: models.UserType = data["user"]

        match = self.regexp_fsm.search(User.fsm)

        if match:
            return {"regexp_fsm": match}
        return False


class AdminFilter(Filter):
    """
    Переопределение is_chat_admin фильтра на тот же, только с кешем
    """

    def __init__(self, is_chat_admin: Optional[Union[ChatIDArgumentType, bool]] = None):
        self._check_current = False
        self._chat_ids = None

        if is_chat_admin is False:
            raise ValueError("is_chat_admin cannot be False")

        if not is_chat_admin:
            self._check_current = True
            return

        if isinstance(is_chat_admin, bool):
            self._check_current = is_chat_admin
        self._chat_ids = extract_chat_ids(is_chat_admin)
        self.validkey = "is_chat_admin"

    @classmethod
    def validate(
        cls, full_config: typing.Dict[str, typing.Any]
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        result = {}

        if "is_chat_admin" in full_config:
            result["is_chat_admin"] = full_config.pop("is_chat_admin")

        return result

    async def check(
        self, obj: Union[types.Message, types.CallbackQuery, types.InlineQuery]
    ) -> bool:
        if self.validkey in obj.conf:
            return obj.conf[self.validkey]
        user_id = obj.from_user.id

        if self._check_current:
            if isinstance(obj, types.Message):
                message = obj
            elif isinstance(obj, types.CallbackQuery) and obj.message:
                message = obj.message
            else:
                obj._conf[self.validkey] = False
                return obj.conf[self.validkey]
            if message.chat.type == types.ChatType.PRIVATE:  # there is no admin in private chats
                obj._conf[self.validkey] = False
                return obj.conf[self.validkey]
            chat_ids = [message.chat.id]
        else:
            chat_ids = self._chat_ids

        admins = [
            member.user.id
            for chat_id in chat_ids
            for member in await obj.bot.get_chat_administrators(chat_id)
        ]
        admins.extend([1087968824, 267519921])  # GroupAnonymousBot
        obj._conf[self.validkey] = user_id in admins

        return obj.conf[self.validkey]


class IsGroupJoin(BoundFilter):
    key = "is_group_join"

    def __init__(self, is_group_join: bool):
        self.is_group_join = is_group_join

    async def check(self, update: types.ChatMemberUpdated):
        # logger.debug(update)
        return (
            update.old_chat_member.status == "left"
            and update.new_chat_member.status == "member"
            and update.chat.type in ("group", "supergroup")
        )


class IsGroupLeft(BoundFilter):
    key = "is_group_left"

    def __init__(self, is_group_left: bool):
        self.is_group_left = is_group_left

    async def check(self, update: types.ChatMemberUpdated):
        # logger.debug(update)
        return update.new_chat_member.status == "left" and update.chat.type in (
            "group",
            "supergroup",
        )


dp.filters_factory.bind(
    GlobalAdminFilter, event_handlers=[dp.message_handlers, dp.callback_query_handlers]
)
dp.filters_factory.unbind(OldAdminFilter)  # Удаляем старый фильтр
dp.filters_factory.bind(
    AdminFilter,
    event_handlers=[
        dp.message_handlers,
        dp.edited_message_handlers,
        dp.channel_post_handlers,
        dp.edited_channel_post_handlers,
        dp.callback_query_handlers,
        dp.inline_query_handlers,
    ],
)
dp.filters_factory.bind(
    FsmFilter, event_handlers=[dp.message_handlers, dp.callback_query_handlers]
)
dp.filters_factory.bind(
    RegexpFsmFilter, event_handlers=[dp.message_handlers, dp.callback_query_handlers]
)
dp.filters_factory.bind(JsonCallbackDataFilter, event_handlers=[dp.callback_query_handlers])
dp.filters_factory.bind(
    IsGroupJoin, event_handlers=[dp.my_chat_member_handlers, dp.chat_member_handlers]
)

logger.debug("filters loaded")
