import logging

from aiogram import Dispatcher
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

from database.database import Database
from tasks import wallet_processing, check_wallet_is_correct


class WalletForm(StatesGroup):
    wallet = State()


wallet_cb = CallbackData('wlt', 'action', 'addr')


async def remove_wallet_callback(callback_query: types.CallbackQuery, db: Database):
    """start wallet input process. part 1"""
    inline_kb = InlineKeyboardMarkup()
    wallets = await db.get_wallets_by_chat(callback_query.message.chat.id)
    for i in wallets:
        inline_kb.add(
            InlineKeyboardButton(i['wallet'][0:10] + "..." + i['wallet'][-4:],
                                 callback_data=wallet_cb.new(action='remove',
                                                             addr=i['wallet'][0:10] + "..." + i['wallet'][-4:]))
        )

    await callback_query.message.reply(
        """Send your address to stop track it’s validators.\n""",
        reply_markup=inline_kb
    )


async def remove_action_callback(callback_query: types.CallbackQuery, callback_data: dict, db: Database):
    logging.info(callback_data['addr'])
    await db.delete_wallet(wallet=callback_data['addr'], chat_id=callback_query.message.chat.id)
    await callback_query.message.reply(
        f"""You removed adress {callback_data['addr']}, you will not get any notifiacation about it.\n
        Do you want to add or remove another address?""",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton('Add address', callback_data='/add_address'),
            InlineKeyboardButton('Remove address', callback_data='/remove_address')
        )
    )


async def add_wallet_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """start wallet input process. part 1"""
    await callback_query.message.reply(
        """Send your address to add and track it’s validators. 
        \nI support this networks: cosmos, juno, akash...""",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton('Cancel', callback_data='/cancel'),
        )
    )
    await state.set_state(WalletForm.wallet)


async def process_wallet(message: types.Message, state: FSMContext, db: Database):
    wallet = message.text
    if len(wallet) < 10:
        await message.reply(
            """❌ Incorrect address, please send it again. 
            \nFor example:
            \ncosmos1gf4wlkutql95j7wwsxz490s6fahlvk2sqj4m34 or juno1lzhlnpahvznwfv4jmay2tgaha5kmz5qx292dgs""",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton('Cancel', callback_data='/cancel'),
            )
        )
        return

    if await check_wallet_is_correct(message.text):
        async with state.proxy() as data:
            data['wallet'] = message.text

            await db.add_wallet(wallet=data['wallet'], chat_id=message.chat.id)

            await message.reply(
                """I added the wallet. I’m checking it’s validators 🔎
                \nI need some time..."""
            )
            await wallet_processing({'wallet': data['wallet'], 'chat_id': message.chat.id}, message.bot, True)
            await state.finish()
    else:
        await message.reply(
            """❌ Incorrect address, please send it again. 
            \nFor example:
            \ncosmos1gf4wlkutql95j7wwsxz490s6fahlvk2sqj4m34 or juno1lzhlnpahvznwfv4jmay2tgaha5kmz5qx292dgs""",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton('Cancel', callback_data='/cancel'),
            )
        )
        return


def register_handlers_wollet(dp: Dispatcher):
    dp.register_callback_query_handler(add_wallet_callback, lambda c: c.data == '/add_address')
    dp.register_callback_query_handler(remove_wallet_callback, lambda c: c.data == '/remove_address')
    dp.register_callback_query_handler(remove_action_callback, wallet_cb.filter())
    dp.register_message_handler(process_wallet, state=WalletForm.wallet)
