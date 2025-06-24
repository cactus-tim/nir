import asyncio
import random
import time
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.errors import InviteRequestSent, InviteHashExpired, UserAlreadyParticipant

from database.req import get_label
from instance import logger, links, messages
from brain.brain import create_message


pending_replies = {}


async def code_finder(msg: str) -> int:
    for i in range(len(msg)):
        try:
            int(msg[i])
            return int(msg[i: i + 5])
        except Exception:
            continue


def setup_handlers(client):
    @client.on_message(filters.private)
    async def reply(client, message):
        user_id = message.from_user.id
        label = await get_label(user_id)
        if not label:
            label = await add_user(user_id)

        if user_id not in pending_replies:
            pending_replies[user_id] = {
                'messages': [message.text],
                'task': asyncio.create_task(handle_pending(client, message.chat.id, label, user_id))
            }
        else:
            pending_replies[user_id]['messages'].append(message.text)

    async def handle_pending(client, chat_id, label, user_id):
        await client.read_chat_history(chat_id)
        messages = pending_replies[user_id]['messages']
        combined_message = "\n".join(messages)
        del pending_replies[user_id]

        await asyncio.sleep(random.randint(10, 70))
        response_text = create_message(label, messages)
        await client.send_chat_action(chat_id, ChatAction.TYPING)
        await asyncio.sleep(random.randint(5, 15))
        await client.send_message(user_id, response_text, disable_notification=True)
