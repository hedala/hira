from pyrogram import Client, filters
from pyrogram.types import Message

from heda import redis, log

@Client.on_message(filters.command(["start"]))
async def handle_start_command(_, message: Message):
    try:
        user_id = message.from_user.id
        start_message = (
            f"Selam! {message.from_user.mention}\n"
        )
        await message.reply_text(
            text=start_message,
            quote=True
        )
    
        log(__name__).info(
            f"{message.command[0]} command was called by {message.from_user.full_name}."
        )

        new_user = await redis.is_added(
            "NEW_USER", user_id
        )
        if not new_user:
            await redis.add_to_db(
                "NEW_USER", user_id
            )

    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")
