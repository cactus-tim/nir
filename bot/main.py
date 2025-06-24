import asyncio
import random
from datetime import datetime, timedelta

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram.errors import UserDeactivatedBan

from confige import BotConfig
from database.req import get_all_bots, get_all_users, delete_bot, update_bot, get_bot_status
from handlers import errors, user
from instance import bot, scheduler, Client, logger, messages
from database.models import async_main
from modules.mes_writer import send_messages
from modules.mes_handler import setup_handlers


async def init_accounts():
    accounts = []
    _accounts = await get_all_bots()
    for account in _accounts:
        client = Client(account.name, api_id=account.api_id, api_hash=account.api_hash)
        accounts.append(client)
    return accounts


def register_routers(dp: Dispatcher) -> None:
    dp.include_routers(errors.router, user.router)


async def progrev(clients):
    for idx, client in enumerate(clients):
        status = await get_bot_status(client.api_id)
        if status != 0:
            continue
        for _ in range(0, len(clients)//3):
            r_id = random.randint(0, len(clients) - 1)
            if r_id == idx:
                continue
            await client.send_message(clients[r_id].name, random.choice(messages))


async def schedule_tasks(clients, users):
    async def daily_task():
        client_id = 0
        for user in users:
            client_id = await send_messages(clients, user.id, client_id=client_id)

    scheduler.add_job(daily_task, 'interval', days=1, start_date='2023-10-01 12:00:00', timezone='Europe/Moscow')
    await daily_task()


async def shutdown(clients):
    for client in clients:
        await client.stop()
    scheduler.shutdown()


async def main() -> None:
    await async_main()

    scheduler.start()

    clients = await init_accounts()
    good_clients = []
    status_updates = [(7, 20), (15, 40), (39, 50)]

    users = await get_all_users()
    await progrev(good_clients)
    await schedule_tasks(good_clients, users)

    try:
        await dp.start_polling(bot, skip_updates=True)
    except Exception as _ex:
        print(f'Exception: {_ex}')
    finally:
        await bot.send_message(483458201, text="We are down")
        await shutdown(good_clients)


if __name__ == '__main__':
    asyncio.run(main())