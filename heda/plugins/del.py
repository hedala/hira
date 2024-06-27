from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.enums import ChatMemberStatus
import time

async def is_admin_or_creator(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        chat_member = await client.get_chat_member(chat_id, user_id)
        return chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        print(f"Kullanıcı yetkisi kontrol edilirken hata oluştu: {e}")
        return False

@Client.on_message(filters.command("del") & filters.group)
async def delete_messages(client: Client, message: Message):
    # Komutu gönderen kişinin admin veya kurucu olup olmadığını kontrol et
    if not await is_admin_or_creator(client, message.chat.id, message.from_user.id):
        await message.reply("Bu komutu sadece adminler ve kurucular kullanabilir.")
        return

    # Komuttan sayıyı al
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

    # Mesajları silme işlemi
    deleted_count = 0
    try:
        async for msg in client.iter_history(message.chat.id, limit=count + 1):
            try:
                await client.delete_messages(message.chat.id, msg.id)
                deleted_count += 1
            except FloodWait as e:
                time.sleep(e.x)  # FloodWait hatasında belirtilen süre kadar bekle
            except Exception as e:
                print(f"Mesaj silinirken hata oluştu: {e}")

        await message.reply(f"{deleted_count - 1} mesaj başarıyla silindi.")
    except Exception as e:
        await message.reply(f"Mesajlar silinirken bir hata oluştu: {e}")
