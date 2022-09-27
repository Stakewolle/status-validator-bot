from aiogram import Dispatcher
from aiogram import md, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.database import Database
from database.user import get_user_by_id


class EmailForm(StatesGroup):
    email = State()


async def send_welcome(message: types.Message, state: FSMContext, db: Database):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    # Set state
    await state.finish()
    users = await get_user_by_id(message.from_id, db)
    inline_kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton('Help', callback_data='/help'),
        InlineKeyboardButton('Wallet', callback_data='/wallet')
    )
    if len(users) == 0:
        await message.reply("""Hi! 👋 I'm a Stakewolle alert bot, I can track and notify your validator status if something happens.
        \n🔔 I can track active, inactive, and jail statuses. 👮It’s important because when your validator is jailed, your funds are slashed, each time when it happens you miss ~1% of your staked funds to this validator. 
        \n💤 And when your validator is inactive, you do not get your rewards. 
        \n💭Both of these states are bad, choosing the right validator is important for your wealth and network health.
        \n🔎You have not added any address yet.
        \n👛Use commands /manage to add or remove wallet and /list to display your wallets.""", reply_markup=inline_kb)
        return
    else:
        res = await db.get_wallets_by_chat(message.chat.id)
        string_res = ""
        for i in res:
            string_res += i['wallet'] + "\n"
        await message.reply(md.text("""Hi! 👋 I'm a Stakewolle alert bot, I can track and notify your validator status if something happens.
        \n🔔 I can track active, inactive, and jail statuses. 👮It’s important because when your validator is jailed, your funds are slashed, each time when it happens you miss ~1% of your staked funds to this validator. 
        \n💤 And when your validator is inactive, you do not get your rewards. 
        \n💭Both of these states are bad, choosing the right validator is important for your wealth and network health.
        \nWe found your wallets, and we are already tracking your validators! 
        \n👛Use commands /manage to add or remove wallet and /list to display your wallets.
        \nYour wallets:\n""" + md.text(string_res)), reply_markup=inline_kb)


def register_handlers_start(dp: Dispatcher):
    dp.register_message_handler(send_welcome, commands=['start', 'help'])
