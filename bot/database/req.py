from sqlalchemy import select, desc, distinct, and_

from database.models import User, async_session
from errors.errors import *
from handlers.errors import db_error_handler


async def add_user(user_id: int) -> str:
    async with async_session() as session:
        user = User(
            id=user_id,
            label="new"
        )
        session.add(user)
        await session.commit()
        return user.label



async def get_label(user_id: int) -> str:
    async with async_session() as session:
        label = await session.scalar(select(User.label).where(User.id == user_id))
