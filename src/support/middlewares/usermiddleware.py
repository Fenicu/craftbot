from datetime import datetime
from typing import Optional, Union

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware
from aioredis.client import Redis
from loguru import logger
from odmantic import AIOEngine

from config import cfg
from support.dbmanager import odmantic_mongo
from support.dbmanager import redis as redis_engine
from support.models import UserType


class UserMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ["error", "update"]

    async def pre_process(
        self,
        update: Union[types.ChatMemberUpdated, types.Message, types.CallbackQuery],
        data: dict,
    ):
        redis = await redis_engine.get_db()
        mongo = odmantic_mongo.get_engine()
        user = await self.validate_user(update, mongo)
        await mongo.save(user)

        data["user"] = user
        data["mongo"] = mongo
        data["redis"] = redis

    async def post_process(
        self,
        update: Union[types.ChatMemberUpdated, types.Message, types.CallbackQuery],
        data: dict,
        *args,
    ):
        mongo: AIOEngine = data["mongo"]
        redis: Redis = data["redis"]
        await redis.close()

    async def validate_user(
        self,
        update: Union[types.Message, types.CallbackQuery, types.ChatMemberUpdated],
        mongo: AIOEngine,
    ) -> UserType:
        if isinstance(update, types.CallbackQuery):
            User = update.from_user

        elif isinstance(update, types.Message):
            User = update.from_user

        elif isinstance(update, types.ChatMemberUpdated):
            User = update.new_chat_member.user

        else:
            logger.warning("Update is not supported {}", types(update))
            raise CancelHandler()

        if User.id == 777000:
            raise CancelHandler()

        if User.is_bot:
            raise CancelHandler()

        user_in_db = await self.get_user(user=User, mongo=mongo)

        if user_in_db.ban and not user_in_db.admin:
            if isinstance(update, types.CallbackQuery):
                await update.answer("Вас усадили на бутылку", show_alert=True)
            raise CancelHandler()

        return user_in_db

    async def get_user(
        self,
        user: types.User,
        mongo: AIOEngine,
    ) -> UserType:
        user_db = await mongo.find_one(UserType, UserType.telegram_id == user.id)
        if not user_db:
            user_db = UserType(
                telegram_id=user.id,
                name=user.full_name,
                username=user.username,
                admin=True if user.id in cfg.telegram_admins else False,
            )
            logger.trace("Новый пользователь: {}", user_db)
        else:
            user_db.name = user.full_name
            user_db.username = user.username
            user_db.admin = True if user.id in cfg.telegram_admins else user_db.admin
            user_db.ban = (
                user_db.ban if not user_db.admin else False
            )  # Если пользователь админ = снимаем бан
        return user_db
