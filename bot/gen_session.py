import asyncio

from pyrogram import Client


async def main(api_id, api_hash, name) -> None:
    async with Client(name, api_id=api_id, api_hash=api_hash) as app:
        session_string = await app.export_session_string()
        print(f"Ваша строка сессии: {session_string}")
        print(f"Ваша строка сессии: {app.session.dc_id}")
        print(f"Ваша строка сессии: {app.session.auth_key}")


if __name__ == '__main__':
    asyncio.run(main(, '', ''))