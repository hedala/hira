import os
import re
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytube import YouTube
from youtubesearchpython import VideosSearch
from heda import redis, log

# Regex to match YouTube URLs
url_regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$"

# Command to search YouTube and display top 5 results
@Client.on_message(filters.command(["sr"]))
async def handle_search_command(client, message: Message):
    try:
        query = " ".join(message.command[1:])
        if not query:
            await message.reply_text("Lütfen bir arama terimi sağlayın. Örneğin: /sr <arama_terimi>")
            return

        videos_search = VideosSearch(query, limit=5)
        results = videos_search.result()["result"]

        if not results:
            await message.reply_text("Sonuç bulunamadı.")
            return

        buttons = []
        for i, result in enumerate(results):
            buttons.append([
                InlineKeyboardButton(
                    text=f"{i + 1}. {result['title']}",
                    callback_data=f"select|{result['id']}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(
            "Arama sonuçları:",
            reply_markup=reply_markup,
            quote=True
        )

        log(__name__).info(
            f"{message.command[0]} command was called by {message.from_user.full_name} with query {query}."
        )

    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")

# Handle selection of a search result
@Client.on_callback_query(filters.regex(r"^select\|"))
async def handle_select_callback(client, callback_query: CallbackQuery):
    try:
        data = callback_query.data.split("|")
        video_id = data[1]

        buttons = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("Video", callback_data=f"dw_video|{video_id}"),
                InlineKeyboardButton("Music", callback_data=f"dw_music|{video_id}")
            ]]
        )
        await callback_query.message.reply_text(
            "Ne tür bir içerik indirmek istiyorsunuz?",
            reply_markup=buttons,
            quote=True
        )

        log(__name__).info(
            f"Video selection {video_id} by {callback_query.from_user.full_name}."
        )

    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")

# Handle download request (video or music)
@Client.on_callback_query(filters.regex(r"^dw_(video|music)\|"))
async def handle_dw_callback(client, callback_query: CallbackQuery):
    try:
        data = callback_query.data.split("|")
        dw_type = data[0]
        video_id = data[1]
        url = f"https://www.youtube.com/watch?v={video_id}"

        await callback_query.message.delete()  # Delete the previous message with buttons
        await callback_query.message.reply_text("İsteğiniz işleniyor, lütfen bekleyin...")

        yt = YouTube(url)
        file_path = str(round(time.time() * 1000))

        if dw_type == "dw_video":
            stream = yt.streams.filter(progressive=True).order_by('resolution').desc().first()
            file_path += ".mp4"
            stream.download(filename=file_path)
            await callback_query.message.reply_video(video=open(file_path, 'rb'))
        elif dw_type == "dw_music":
            stream = yt.streams.filter(only_audio=True).first()
            file_path += ".mp3"
            stream.download(filename=file_path)
            await callback_query.message.reply_audio(audio=open(file_path, 'rb'))

        os.remove(file_path)
        log(__name__).info(
            f"{dw_type} download for {url} by {callback_query.from_user.full_name} completed."
        )

    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")
        await callback_query.message.reply_text("Bir hata oluştu. Lütfen tekrar deneyin.")

# Command to directly download YouTube videos
@Client.on_message(filters.command(["dw"]))
async def handle_dw_command(client, message: Message):
    try:
        user_id = message.from_user.id
        command_params = message.text.split()
        if len(command_params) != 2:
            await message.reply_text("Lütfen bir YouTube linki sağlayın. Örneğin: /dw <youtube_link>")
            return

        youtube_link = command_params[1]
        if not re.match(url_regex, youtube_link):
            await message.reply_text("Geçerli bir YouTube linki sağlayın.")
            return

        buttons = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("Video", callback_data=f"dw_video|{youtube_link.split('v=')[1]}"),
                InlineKeyboardButton("Music", callback_data=f"dw_music|{youtube_link.split('v=')[1]}")
            ]]
        )
        await message.reply_text(
            "Ne tür bir içerik indirmek istiyorsunuz?",
            reply_markup=buttons,
            quote=True
        )

        log(__name__).info(
            f"{message.command[0]} command was called by {message.from_user.full_name} with link {youtube_link}."
        )

    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")
