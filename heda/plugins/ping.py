import os
import time
import wget
import yt_dlp
import speedtest
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from heda import redis, log

@Client.on_message(filters.command(["ping"]))
async def handle_ping_command(client: Client, message: Message):
    try:
        start_time = time.time()
        sent_message = await message.reply_text("Pong!")
        end_time = time.time()
        ping_time = (end_time - start_time) * 1000
        await sent_message.edit_text(f"`Pong! {int(ping_time)} ms`")
        log(__name__).info(
            f"{message.command[0]} command was called by {message.from_user.full_name} with ping time {int(ping_time)} ms."
        )
    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")

@Client.on_message(filters.command(["id"]))
async def handle_id_command(_, message: Message):
    try:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            group_id = message.chat.id
            await message.reply_text(
                f"Alıntılanan Kişinin ID'si: `{user_id}`\n"
                f"Grup ID'si: `{group_id}`"
            )
        else:
            user_id = message.from_user.id
            group_id = message.chat.id
            await message.reply_text(
                f"Sizin ID'niz: `{user_id}`\n"
                f"Grup ID'si: `{group_id}`"
            )
        log(__name__).info(
            f"{message.command[0]} command was called by {message.from_user.full_name}."
        )
    except Exception as e:
        log(__name__).error(f"Error: {str(e)}") 
