from typing import List

from database.database import Database


async def get_user_by_id(from_id: int, db: Database) -> List[dict]:
    """get users from db from_id - telegram integer id"""
    sql = "SELECT * FROM users where from_id = $1"
    async with db.pool.acquire() as connection:
        async with connection.transaction():
            rows = await connection.fetch(sql, from_id)
            return [dict(row) for row in rows]


async def create_user(email: str, chat_id: int, from_id: int, db: Database) -> None:
    """get users from db from_id - telegram integer id"""
    sql = "INSERT INTO users (email,chat_id,from_id) VALUES ($1,$2,$3) ON CONFLICT (email,from_id) DO NOTHING;"
    await db.pool.execute(sql, email, chat_id, from_id)
