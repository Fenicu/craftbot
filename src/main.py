import random

from aiogram import executor, types
from aiogram.contrib.middlewares import logging
from aiogram.dispatcher.webhook import configure_app
from aiohttp import web
from aiohttp.web_app import Application
from aiohttp.web_request import Request
from loguru import logger

import addons
from config import allowed_updates, cfg
from support.bots import bot, dp
from support.middlewares import ThrottlingMiddleware, UserMiddleware

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


async def on_startup(app: Application):
    logger.info("Получаю информацию о боте...")
    botinfo = await dp.bot.me
    if not cfg.is_polling:
        logger.warning("Устанавливаю вебхук {}", cfg.webhook_url)
        await bot.set_webhook(
            cfg.webhook_url,
            allowed_updates=allowed_updates,
            drop_pending_updates=True,
            max_connections=cfg.wh_max_connections,
        )
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
