import asyncio
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, \
    InlineKeyboardButton

from database.database import Database
from handlers.start import register_handlers_start
from handlers.wallet import register_handlers_wollet
from middleware.DBMiddleware import DBMiddleware
from tasks import on_bot_start_up
import os

# bot token
API_TOKEN = os.environ.get("TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
loop = asyncio.get_event_loop()
db = Database(loop)
bot = Bot(token=API_TOKEN)

# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage, loop=loop)


@dp.callback_query_handler(lambda c: c.data == '/help')
async def help_callback_button(callback_query: types.CallbackQuery):
    """help callback"""
    inline_kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton('Wallet', callback_data='/wallet')
    )
    await callback_query.message.reply("""Help
    \nHi! 👋 I'm a Stakewolle alert bot, I can track and notify your validator status if something happens.
    \n🔔 I can track active, inactive, and jail statuses. 👮It’s important because when your validator is jailed, your funds are slashed, each time when it happens you miss ~1% of your staked funds to this validator. 
    \nI support this networks: cosmos, juno, akash...
    \n💤 And when your validator is inactive, you do not get your rewards.
    \n💭Both of these states are bad, choosing the right validator is important for your wealth and network health.
    \n🔎You have not added any address yet.
    \n👛Use command /wallet to manage your addresses.
    \nIf you have any questions you can wrtie to @stakewolle chat.""",
                                       reply_markup=inline_kb)


# You can use state '*' if you need to handle all states
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
@dp.callback_query_handler(lambda c: c.data == '/cancel')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())


@dp.callback_query_handler(lambda c: c.data == '/cancel', state='*')
async def cancel_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await callback_query.message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands='wallet')
async def wallet_message_handler(message: types.Message):
    """wollet main message"""
    res = await db.get_wallets_by_chat(message.chat.id)  # get user wallets by chat id
    string_wallets = ""
    for i in res:
        string_wallets += i['wallet'] + "\n"

    inline_kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton('Add address', callback_data='/add_address'),
        InlineKeyboardButton('Remove address', callback_data='/remove_address')
    )
    reply_message = "*Wallet*\n"

    if len(string_wallets) == 0:
        reply_message += "🔎You have not added any address yet."
    else:
        reply_message += string_wallets

    await message.reply(reply_message, reply_markup=inline_kb)


@dp.callback_query_handler(lambda c: c.data == '/wallet')
async def wallet_callback_button(callback_query: types.CallbackQuery):
    """wollet main message"""
    res = await db.get_wallets_by_chat(callback_query.message.chat.id)  # get user wallets by chat id
    string_wallets = ""
    for i in res:
        string_wallets += i['wallet'] + "\n"

    inline_kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton('Add address', callback_data='/add_address'),
        InlineKeyboardButton('Remove address', callback_data='/remove_address')
    )
    reply_message = "*Wallet*\n"

    if len(string_wallets) == 0:
        reply_message += "🔎You have not added any address yet."
    else:
        reply_message += string_wallets

    await callback_query.message.reply(reply_message, reply_markup=inline_kb)


if __name__ == '__main__':
    dp.middleware.setup(DBMiddleware(db))
    register_handlers_start(dp)
    register_handlers_wollet(dp)
    executor.start_polling(dp, skip_updates=True, on_startup=on_bot_start_up)
