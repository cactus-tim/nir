import asyncio
import os
import json
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.enums.chat_type import ChatType


SESSION_NAME = ""
API_ID =
API_HASH = ""
DEPTH_MONTHS = 36
THRESHOLD_K = 100
OUTPUT_DIR = "../dialogs"


async def fetch_history_throttled(app: Client, chat_id: int,
                                  batch_size: int = 100,
                                  delay: float = 1.0):
    offset_id = 0
    while True:
        batch = []
        try:
            async for msg in app.get_chat_history(
                    chat_id,
                    limit=batch_size,
                    offset_id=offset_id
            ):
                batch.append(msg)
        except FloodWait as e:
            print(f"[{chat_id}] FloodWait: сплю {e.x}s…")
            await asyncio.sleep(e.x + 1)
            continue
        if not batch:
            break
        for msg in batch:
            yield msg
        offset_id = batch[-1].id - 1
        await asyncio.sleep(delay)


async def export_dialogs(session_name: str, api_id: int, api_hash: str,
                   depth_months: int, threshold_k: int, output_dir: str):
    cutoff = datetime.utcnow() - relativedelta(months=depth_months)

    app = Client(session_name, api_id=api_id, api_hash=api_hash)
    os.makedirs(output_dir, exist_ok=True)

    async with app:
        async for dialog in app.get_dialogs():
            chat = dialog.chat
            if chat.type != ChatType.PRIVATE:
                continue

            chat_id = chat.id
            recent_msgs = []
            try:
                async for msg in fetch_history_throttled(app, chat_id):
                    if msg.date < cutoff:
                        break
                    recent_msgs.append(msg)
            except FloodWait as e:
                print(f"FloodWait: sleeping {e.x}s when counting messages in {chat_id}")
                await asyncio.sleep(e.x)
                continue

            if len(recent_msgs) <= threshold_k:
                continue

            messages = []
            try:
                for message in recent_msgs:
                    messages.append({
                        "date": str(message.date.isoformat()),
                        "recepeint": "me" if message.from_user.id == 483458201 else "second_person", # 483458201
                        "chat_id": str(message.chat.id),
                        "text": str(message.text) or str(message.caption) or "Some media file",
                    })
            except FloodWait as e:
                print(f"FloodWait: sleeping {e.x}s when fetching history from {chat_id}")
                await asyncio.sleep(e.x)
                continue

            if not messages:
                continue

            chat_title = (chat.first_name or chat.last_name or f"chat_{chat_id}").replace(os.sep, "_")
            filename = os.path.join(output_dir, f"{chat_title}_{chat_id}.json")

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "chat": {"id": chat_id, "title": chat_title},
                    "messages": messages
                }, f, ensure_ascii=False, indent=2)

            print(f"Exported {len(messages)} messages from '{chat_title}' to {filename}")


async def main():
        print(f"Starting export: sessions={SESSION_NAME}, months={DEPTH_MONTHS}, threshold={THRESHOLD_K}, output='{OUTPUT_DIR}'")
        await export_dialogs(
            session_name=SESSION_NAME,
            api_id=API_ID,
            api_hash=API_HASH,
            depth_months=DEPTH_MONTHS,
            threshold_k=THRESHOLD_K,
            output_dir=OUTPUT_DIR
        )


if __name__ == "__main__":
    asyncio.run(main())
