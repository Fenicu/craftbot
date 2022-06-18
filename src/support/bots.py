from aiogram import Bot
from aiogram.dispatcher import Dispatcher

from config import cfg
from support.i18n import I18nMiddleware

bot = Bot(
    token=cfg.telegram_token,
    validate_token=True,
    parse_mode="HTML",
    server=cfg.bot_api_server,
)
dp = Dispatcher(
    bot, storage=cfg.fsm_storage
)  # run_tasks_by_default возвращает в вебхук тру, даже если задача затупила

i18n = I18nMiddleware("BotLocale", "./locale", default="ru")

_ = i18n.gettext

__all__ = ["bot", "dp", "i18n", "_"]
