import asyncio
from typing import Callable, Dict, Any, Awaitable

from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from database.database import Database


class DBMiddleware(BaseMiddleware):
    def __init__(self, db: Database):
        self.db = db
        super(DBMiddleware, self).__init__()

    async def on_pre_process_message(self, message: Message, data: dict):
        data["db"] = self.db

    async def on_pre_process_callback_query(self, message: Message, data: dict):
        data["db"] = self.db
