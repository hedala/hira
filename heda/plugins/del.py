from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, MessageDeleteForbidden
import asyncio

async def is_admin_or_creator(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        chat_member = await client.get_chat_member(chat_id, user_id)
        return chat_member.status in ["administrator", "creator"]
    except Exception as e:
        print(f"Kullanıcı yetkisi kontrol edilirken hata oluştu: {e}")
        return False

@Client.on_message(filters.command("del") & filters.group)
async def delete_messages(client: Client, message: Message):
    if not await is_admin_or_creator(client, message.chat.id, message.from_user.id):
        await message.reply("Bu komutu sadece adminler ve kurucular kullanabilir.")
        return

    if len(message.command) != 2:
        await message.reply("Doğru kullanım: /del <sayı>")
        return

    try:
        count = int(message.command[1])
        if count <= 0:
            await message.reply("Lütfen pozitif bir sayı girin.")
            return
    except ValueError:
        await message.reply("Geçerli bir sayı giriniz.")
        return

    deleted_count = 0
    try:
        # Silinecek mesajların ID'lerini toplama
        message_ids = []
        async for msg in client.get_chat_history(message.chat.id, limit=count + 1):
            message_ids.append(msg.id)

        # Mesajları toplu olarak silme
        await client.delete_messages(message.chat.id, message_ids)
        deleted_count = len(message_ids) - 1  # Komut mesajını sayma

        await message.reply(f"{deleted_count} mesaj başarıyla silindi.")
    except FloodWait as e:
        await asyncio.sleep(e.x)
        await message.reply(f"Çok fazla istek nedeniyle {e.x} saniye beklendi. Lütfen tekrar deneyin.")
    except MessageDeleteForbidden:
        await message.reply("Bazı mesajları silme yetkim yok. Silinebilenler silindi.")
    except Exception as e:
        await message.reply(f"Mesajlar silinirken bir hata oluştu: {str(e)}")
