import asyncio
import logging
import re

from aiogram import Bot, Dispatcher

from database.database import Database
from registry import Registry

loop = asyncio.get_event_loop()
db = Database(loop)


async def check_wallet_is_correct(wallet: str) -> bool:
    logging.info(wallet)
    chains = await db.get_chains()
    prefix = re.match(r'[a-z]*', wallet).group()
    logging.info(f'prefix: {prefix}')

    if prefix is not None:
        for i in chains:
            if i['bech32_prefix'] == prefix:
                registry = Registry(chain_name=i['chain_name'], db=db)
                return await registry.check_wallet_is_correct(wallet)
    else:
        return False


async def wallet_processing(wallet: dict, bot: Bot, need_callback: bool) -> None:
    logging.info(wallet)
    chains = await db.get_chains()
    prefix = re.match(r'[a-z]*', wallet['wallet']).group()
    logging.info(f'prefix: {prefix}')

    inactive_validators = []
    wallet_validators_moniker = []

    if prefix is not None:
        for i in chains:
            if i['bech32_prefix'] == prefix:
                registry = Registry(chain_name=i['chain_name'], db=db)
                wallet_validators = await registry.get_validators_by_wallet(wallet['wallet'])
                logging.info(f'wallet validators is:{wallet_validators}')
                chain_validators = await registry.get_chain_validators()

                for w_validator in wallet_validators:
                    for c_validator in chain_validators:
                        if w_validator == c_validator['operator_address'] and await registry.check_delegated_balance(wallet['wallet'],w_validator):
                            wallet_validators_moniker.append(c_validator['description']['moniker'])
                            if c_validator['status'] == 'BOND_STATUS_UNBONDED':
                                inactive_validators.append(c_validator['description']['moniker'])
                break
    logging.info(f"inactive validators: {inactive_validators}")
    if len(inactive_validators) > 0:
        tg_message = """‼️Validators of address {0} is INACTIVE ‼️\n{1} \nRedelegate to another Validator!""".format(
            wallet['wallet'][0:10] + "..." + wallet['wallet'][-4:], "\n".join(inactive_validators)
        )
        logging.info("send message")
        await bot.send_message(
            wallet['chat_id'],
            tg_message
        )

    elif need_callback:
        tg_message = """
        ✅ All of the validators are active, or you haven’t stake yet.
        \nYour validators: \n{0}
        \n⚠ If one of your validators will be inactive or jailed , I will send you a notification and repeat it every 3 hours until you redelegate your tokens.
        """.format("\n".join(wallet_validators_moniker))
        logging.info("send message")
        await bot.send_message(
                wallet['chat_id'],
                tg_message
        )


async def sync_chains() -> None:
    """cache chains info"""
    while True:
        registry = Registry(chain_name=None, db=db)
        chains_list = await registry.get_chain_registry()
        for i in chains_list:
            if 'chain_name' not in i:
                continue
            if i['chain_name'] is None:
                continue
            await db.save_chain(i)
            logging.info(f"chain: {i['chain_name']} saved to db")
        logging.info("chains update done")
        await asyncio.sleep(60 * 60 * 6)


async def validator_blocks_check() -> None:
    """check missed blocks"""
    # TODO get consensus pubkey
    # https://discord.com/channels/669268347736686612/884005201172910120/989461293134131242
    # TODO get missed blocks info
    # https://cosmos-lcd.quickapi.com/cosmos/slashing/v1beta1/signing_infos
    pass


async def background_on_start(bot: Bot) -> None:
    """background task which is created when bot starts"""
    while True:
        # get all wallets
        wallets = await db.get_wallets()
        logging.info(wallets)
        for wallet in wallets:
            logging.info("...Start process wallet...")
            try:
                await wallet_processing(wallet, bot, False)
            except Exception as ex:
                logging.error(ex)
        logging.info("...Start Job...")
        await asyncio.sleep(60 * 60 * 3)


async def send_message_by_wallet(wallet: dict, bot: Bot, message: str) -> None:
    logging.info(wallet)

    logging.info("send message")
    await bot.send_message(
        wallet['chat_id'],
        message
    )


async def broadcast_news(bot: Bot) -> None:
    logging.info("...Start NEWS Job...")
    while True:
        wallets = await db.get_wallets()
        news = await db.get_news()

        if len(news) == 0:
            logging.info("NO NEWS!")
            return

        for wallet in wallets:
            logging.info("...Start process wallet...")
            try:
                await send_message_by_wallet(wallet, bot, news[0]['news_message'])
            except Exception as ex:
                logging.error(ex)

        await db.clear_news() #clear news
        await asyncio.sleep(30 * 1)

async def on_bot_start_up(dp: Dispatcher) -> None:
    """List of actions which should be done before bot start"""
    # TODO refactor to aioshedule https://pypi.org/project/aioschedule/
    asyncio.create_task(background_on_start(dp.bot))
    asyncio.create_task(sync_chains())
    asyncio.create_task(broadcast_news(dp.bot))
