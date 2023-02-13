from contextlib import suppress
from typing import List

from aiogram import executor, types
from aiogram.contrib.middlewares import logging
from aiogram.dispatcher.webhook import configure_app
from aiohttp import web
from aiohttp.web_app import Application
from aiohttp.web_request import Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

import addons
from config import allowed_updates, cfg
from support.bots import bot, dp
from support.dbmanager.FastMongo import odmantic_mongo
from support.middlewares import ThrottlingMiddleware, UserMiddleware
from support.models.blueprint_model import BlueprintType, TierType
from support.models.items_model import EmbeddedItemType, ItemType
from support.models.user_model import UserType

logging_middleware = logging.LoggingMiddleware()
logging_middleware.logger = logger
# dp.middleware.setup(logging_middleware)  # ALL LOGGING
dp.middleware.setup(UserMiddleware())  # Мидлварь для моделей
dp.middleware.setup(ThrottlingMiddleware(limit=0.6))  # Мидлварь для троттлинга


@dp.errors_handler(run_task=True)
async def errors(update: types.Update, error: Exception):
    logger.exception("Странная ошибка, {}", error)
    return True


@dp.callback_query_handler(text="delete-keyboard")
async def delete_callback(call: types.CallbackQuery):
    await call.message.delete_reply_markup()
    await call.answer()


@dp.callback_query_handler()
async def any_callback(call: types.CallbackQuery):
    await call.answer("🛑🛑🛑", show_alert=True)


async def evaluation_update():
    mongo = odmantic_mongo.get_engine()
    users = mongo.find(
        UserType,
        UserType.bag.items != [],
        sort=UserType.bag.last_update.desc(),
    )
    all_items: List[EmbeddedItemType] = []
    async for user in users:
        for item in user.bag.items:
            item: EmbeddedItemType
            for item_ in all_items:
                if item.item_id == item_.item_id:
                    item_.count += item.count
                    break
            else:
                all_items.append(item)

    best_tier = await mongo.find_one(TierType, sort=TierType.tier_id.desc())
    crafts_in_tier = await mongo.find(BlueprintType, BlueprintType.tier == best_tier.id)
    if len(crafts_in_tier) > 8:
        best_tier = await mongo.find_one(
            TierType,
            TierType.tier_id == best_tier.tier_id - 1,
        )
        crafts_in_tier = await mongo.find(
            BlueprintType,
            BlueprintType.tier == best_tier.id,
        )
    items_in_craft: List[EmbeddedItemType] = []
    for craft in crafts_in_tier:
        for item in craft.items:
            for item_ in items_in_craft:
                if item.item_id == item_.item_id:
                    item_.count += item.count
                    break
            else:
                items_in_craft.append(item)

    items = []
    for item in all_items:
        for needed_item in items_in_craft:
            if needed_item.item_id == item.item_id:
                item_obj = await mongo.find_one(ItemType, ItemType.id == item.item_id)
                old_evaluation = item_obj.evaluation
                item_obj.evaluation = needed_item.count / item.count
                if old_evaluation != item_obj.evaluation:
                    items.append(item_obj)
                    logger.trace(
                        "Обновлена цена для {}: {} -> {}",
                        item_obj.name,
                        old_evaluation,
                        item_obj.evaluation,
                    )
                break
    if items:
        await mongo.save_all(items)


async def on_startup(app: Application):
    logger.info("Получаю информацию о боте...")
    botinfo = await bot.me
    if not cfg.is_polling:
        logger.warning("Устанавливаю вебхук {}", cfg.webhook_url)
        await bot.set_webhook(
            cfg.webhook_url,
            allowed_updates=allowed_updates,
            drop_pending_updates=True,
            max_connections=cfg.wh_max_connections,
        )
    scope = types.BotCommandScopeAllPrivateChats()
    commands = [
        types.BotCommand(command="start", description="Начать работу с ботом"),
        types.BotCommand(command="clear", description="Очистить инвентарь"),
    ]
    await bot.set_my_commands(commands=commands, scope=scope)

    with suppress(Exception):
        await evaluation_update()

    scheduler = AsyncIOScheduler(timezone=cfg.TZ)
    scheduler.add_job(evaluation_update, "interval", hours=1)
    scheduler.start()

    logger.warning("Бот {} [@{}] запущен", botinfo.full_name, botinfo.username)


async def on_shutdown(app: Application):
    logger.warning("Выключаюсь..")
    if not cfg.is_polling:
        await bot.delete_webhook(drop_pending_updates=True)
    await dp.storage.close()
    await dp.storage.wait_closed()
    await bot.session.close()


async def health_check(request: Request):
    return web.json_response({"ok": True})


if __name__ == "__main__":
    if cfg.is_polling:
        executor.start_polling(
            dp,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            allowed_updates=allowed_updates,
            skip_updates=True,
        )
    else:
        app = web.Application()
        app.on_startup.append(on_startup)
        app.on_shutdown.append(on_shutdown)
        configure_app(dp, app, path=cfg.webhook_path)
        if cfg.health_check_path:
            app.add_routes([web.get(cfg.health_check_path, health_check)])
        logger.info("Запускаю вебсервер на {}:{}", cfg.webhook_host, cfg.webhook_port)
        web.run_app(app, host=cfg.webhook_host, port=cfg.webhook_port)
