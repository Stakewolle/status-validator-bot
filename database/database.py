import asyncio
import os
from typing import List, Dict

import asyncpg


class Database:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.pool = loop.run_until_complete(
            asyncpg.create_pool(
                user=os.environ.get('POSTGRES_USER'),
                password=os.environ.get('POSTGRES_PASSWORD'),
                host='postgres',
                database=os.environ.get('POSTGRES_DB_NAME'),
                port='5432',
                max_inactive_connection_lifetime=6
            )
        )

    async def get_rest(self, chain: str) -> List[dict]:
        sql = "SELECT * FROM apis where chain_name = $1"
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                rows = await connection.fetch(sql, chain)
                return [dict(row) for row in rows]

    async def get_chains(self) -> List[dict]:
        """get chains from db"""
        sql = "SELECT * FROM chains"
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                rows = await connection.fetch(sql)
                return [dict(row) for row in rows]

    async def save_chain(self, chain: Dict) -> None:
        """save chains to db"""
        if 'chain_name' not in chain:
            return

        sql = """INSERT INTO chains (chain_name, bech32_prefix) VALUES ($1, $2)
                ON CONFLICT (chain_name) DO NOTHING;"""
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                await self.pool.execute(sql, chain['chain_name'], chain['bech32_prefix'])

        for i in chain['rpcs']:
            sql = """INSERT INTO apis (chain_name, rest_url) VALUES ($1, $2)
                     ON CONFLICT (chain_name,rest_url) DO NOTHING;"""
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    await self.pool.execute(sql, chain['chain_name'], i['address'])

    async def add_wallet(self, wallet: str, chat_id: int) -> None:
        """save wallet to db"""
        sql = "INSERT INTO wallets (wallet, chat_id) VALUES ($1, $2) ON CONFLICT (wallet, chat_id) DO NOTHING;"
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                await self.pool.execute(sql, wallet, chat_id)

    async def delete_wallet(self, wallet: str, chat_id: int) -> None:
        """delete wallet from db"""
        sql = "delete from wallets WHERE wallet like $1 and chat_id=$2;"
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                await self.pool.execute(sql, wallet.replace('...', '%%'), chat_id)

    async def get_wallets_by_chat(self, chat_id: int) -> List:
        """get wallets by chat id"""
        sql = "SELECT wallets.*, users.email FROM wallets LEFT join users on users.chat_id = wallets.chat_id where " \
              "wallets.chat_id = $1 "
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                rows = await connection.fetch(sql, chat_id)
                return [dict(row) for row in rows]

    async def get_wallets(self) -> List:
        """get all wallets"""
        sql = "SELECT wallets.*, users.email FROM wallets LEFT join users on users.chat_id = wallets.chat_id;"
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(sql)
            return [dict(row) for row in rows]

    async def get_news(self) -> List:
        """get all news"""
        sql = "SELECT * FROM news;"
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(sql)
            return [dict(row) for row in rows]

    async def clear_news(self) -> List:
        """get all news"""
        sql = "DELETE FROM news;"
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(sql)
            return [dict(row) for row in rows]
