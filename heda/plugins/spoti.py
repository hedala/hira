import os
import asyncio
import time
from typing import Optional, Dict
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from yt_dlp import YoutubeDL
from mutagen.mp3 import MP3, EasyMP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1
import aiohttp
from pyrogram import Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from pyrogram.errors import FloodWait

# Yapılandırma (üretimde bunları ayrı bir yapılandırma dosyasına taşıyın)
SPOTIPY_CLIENT_ID = ''
SPOTIPY_CLIENT_SECRET = ''
SPOTIPY_REDIRECT_URI = 'https://t.me/hedala'
TELEGRAM_API_ID = 6
TELEGRAM_API_HASH = 'eb06d4abfb49dc3eeb1aeb98ae0f581e'
TELEGRAM_BOT_TOKEN = ''
CHANNEL_ID = -1002239052069

# Spotify ve Telegram kurulumu
sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET,
                        redirect_uri=SPOTIPY_REDIRECT_URI, scope="user-read-currently-playing",
                        cache_path=os.path.join(os.getcwd(), '.spotify_cache'))

app = Client("spotify_bot", api_id=TELEGRAM_API_ID, api_hash=TELEGRAM_API_HASH, bot_token=TELEGRAM_BOT_TOKEN)

async def get_spotify_client() -> spotipy.Spotify:
    token_info = sp_oauth.get_cached_token()
    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        print(f"Please navigate here: {auth_url}")
        response = input("Enter the URL you were redirected to: ")
        code = sp_oauth.parse_response_code(response)
        token_info = sp_oauth.get_access_token(code)
    return spotipy.Spotify(auth=token_info['access_token'])

async def get_current_track(sp: spotipy.Spotify) -> Optional[Dict]:
    try:
        current_track = sp.current_user_playing_track()
        if current_track and current_track['item']:
            return {
                'track_name': current_track['item']['name'],
                'artist_name': current_track['item']['artists'][0]['name'],
                'track_link': current_track['item']['external_urls']['spotify'],
                'artist_link': current_track['item']['artists'][0]['external_urls']['spotify'],
                'thumbnail_url': current_track['item']['album']['images'][0]['url'],
                'duration_ms': current_track['item']['duration_ms']
            }
    except Exception as e:
        print(f"Error getting current track: {e}")
    return None

async def download_song(song_name: str) -> Optional[str]:
    file_path = f"{song_name}.mp3"
    if os.path.exists(file_path):
        return file_path

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'outtmpl': f'{song_name}.%(ext)s',
        'no_warnings': True,
        'quiet': True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(f"ytsearch:{song_name} audio", download=True)
            return file_path
    except Exception as e:
        print(f"Error downloading song: {e}")
    return None

async def add_metadata(file_path: str, track_info: Dict):
    try:
        audio = MP3(file_path, ID3=ID3)
        
        # Add title and artist
        audio.tags.add(TIT2(encoding=3, text=track_info['track_name']))
        audio.tags.add(TPE1(encoding=3, text=track_info['artist_name']))
        
        # Add thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(track_info['thumbnail_url']) as response:
                if response.status == 200:
                    pic = await response.read()
                    audio.tags.add(
                        APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=pic)
                    )
        audio.save()
    except Exception as e:
        print(f"Error adding metadata: {e}")

async def update_pin_message(message_id: int, track_info: Dict) -> bool:
    try:
        # Prepare the new media with caption and buttons
        keyboard = [
            [InlineKeyboardButton("Listen on Spotify", url=track_info['track_link']),
             InlineKeyboardButton("Artist on Spotify", url=track_info['artist_link'])]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        caption = f"🎵 {track_info['track_name']} by {track_info['artist_name']}"
        
        new_media = InputMediaPhoto(
            media=track_info['thumbnail_url'],
            caption=caption
        )
        
        # Update the message with new media, caption, and buttons in a single call
        await app.edit_message_media(
            chat_id=CHANNEL_ID,
            message_id=message_id,
            media=new_media,
            reply_markup=reply_markup
        )
        return True
    except FloodWait as e:
        print(f"FloodWait: sleeping for {e.x} seconds")
        await asyncio.sleep(e.x)
        return False
    except Exception as e:
        print(f"Error updating pin message: {e}")
        return False

async def send_initial_pin_message(track_info: Dict) -> Optional[int]:
    try:
        keyboard = [
            [InlineKeyboardButton("Listen on Spotify", url=track_info['track_link']),
             InlineKeyboardButton("Artist on Spotify", url=track_info['artist_link'])]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        caption = f"🎵 {track_info['track_name']} by {track_info['artist_name']}"
        
        message = await app.send_photo(
            chat_id=CHANNEL_ID,
            photo=track_info['thumbnail_url'],
            caption=caption,
            reply_markup=reply_markup
        )
        await app.pin_chat_message(chat_id=CHANNEL_ID, message_id=message.id)
        return message.id
    except Exception as e:
        print(f"Error sending initial pin message: {e}")
        return None

async def send_song_to_channel(file_path: str):
    try:
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:
            print(f"File size exceeds Telegram's limit: {file_size} bytes")
            return
        with open(file_path, 'rb') as audio:
            await app.send_audio(chat_id=CHANNEL_ID, audio=audio)
    except Exception as e:
        print(f"Error sending song to channel: {e}")

async def check_and_update_track(sp: spotipy.Spotify, last_track: Optional[Dict], pinned_message_id: Optional[int]):
    current_track = await get_current_track(sp)
    if current_track:
        if current_track != last_track:
            print(f"Currently playing: {current_track['track_name']} by {current_track['artist_name']}")
            
            if pinned_message_id is None:
                # İlk çalıştırma, yeni pin mesajı gönder
                pinned_message_id = await send_initial_pin_message(current_track)
                print("Initial pin message sent")
            else:
                # Mevcut pin mesajını güncelle
                success = await update_pin_message(pinned_message_id, current_track)
                if success:
                    print("Pin message updated successfully")
                else:
                    print("Failed to update pin message, sending new pin message")
                    pinned_message_id = await send_initial_pin_message(current_track)
            
            # Download and process the song
            song_name = f"{current_track['artist_name']} - {current_track['track_name']}"
            downloaded_file = await download_song(song_name)
            if downloaded_file and os.path.exists(downloaded_file):
                await add_metadata(downloaded_file, current_track)
                await send_song_to_channel(downloaded_file)
            else:
                print(f"File not found or download failed: {song_name}")
            
            return current_track, pinned_message_id
        else:
            print("Same track is still playing.")
    else:
        print("No track is currently playing.")
    
    return last_track, pinned_message_id

async def main():
    sp = await get_spotify_client()
    last_track = None
    pinned_message_id = None

    while True:
        last_track, pinned_message_id = await check_and_update_track(sp, last_track, pinned_message_id)
        await asyncio.sleep(20)  # Check every 20 seconds

async def run_bot():
    await app.start()
    print("Bot started. Press Ctrl+C to stop.")
    await main()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_bot())
    except KeyboardInterrupt:
        print("Bot stopped.")
      