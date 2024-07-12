import os
import time
import asyncio
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from yt_dlp import YoutubeDL
from mutagen.mp3 import MP3, EasyMP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TRCK, TYER, TCON, TDRC
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Spotify API kimlik bilgileri
SPOTIPY_CLIENT_ID = ''
SPOTIPY_CLIENT_SECRET = ''
SPOTIPY_REDIRECT_URI = 'https://t.me/hedala'

scope = "user-read-currently-playing"

cache_path = os.path.join(os.getcwd(), '.spotify_cache')

sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                        client_secret=SPOTIPY_CLIENT_SECRET,
                        redirect_uri=SPOTIPY_REDIRECT_URI,
                        scope=scope,
                        cache_path=cache_path)

token_info = sp_oauth.get_cached_token()

if not token_info:
    auth_url = sp_oauth.get_authorize_url()
    print(f"Please navigate here: {auth_url}")
    response = input("Enter the URL you were redirected to: ")
    code = sp_oauth.parse_response_code(response)
    token_info = sp_oauth.get_access_token(code)

sp = spotipy.Spotify(auth=token_info['access_token'])

def get_current_track():
    current_track = sp.current_user_playing_track()
    if current_track is not None:
        track_name = current_track['item']['name']
        artist_name = current_track['item']['artists'][0]['name']
        track_link = current_track['item']['external_urls']['spotify']
        artist_link = current_track['item']['artists'][0]['external_urls']['spotify']
        thumbnail_url = current_track['item']['album']['images'][0]['url']
        duration_ms = current_track['item']['duration_ms']
        return {
            'track_name': track_name,
            'artist_name': artist_name,
            'track_link': track_link,
            'artist_link': artist_link,
            'thumbnail_url': thumbnail_url,
            'duration_ms': duration_ms
        }
    else:
        return None

def download_song(song_name):
    search_query = f"{song_name} audio"
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    ]
    for user_agent in user_agents:
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'outtmpl': f'{song_name}.%(ext)s',
            'quiet': True,
            'default_search': 'ytsearch1',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'http_headers': {
                'User-Agent': user_agent
            }
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(search_query, download=True)
                file_path = ydl.prepare_filename(info_dict)
                # Ensure the file has the correct extension
                if not file_path.endswith('.mp3'):
                    file_path = file_path.rsplit('.', 1)[0] + '.mp3'
                # Rename the file to ensure it has the correct extension
                if os.path.exists(file_path):
                    os.rename(file_path, file_path)
                else:
                    # If the file does not exist, try to find the correct file
                    base, ext = os.path.splitext(file_path)
                    possible_files = [f for f in os.listdir('.') if f.startswith(base)]
                    if possible_files:
                        file_path = possible_files[0]
                return file_path
        except Exception as e:
            print(f"Failed with user-agent {user_agent}: {e}")
    return None

def add_metadata(file_path, track_info):
    audio = EasyMP3(file_path)
    audio['title'] = track_info['track_name']
    audio['artist'] = track_info['artist_name']
    audio['album'] = track_info['track_name']
    audio['tracknumber'] = '1'
    audio['date'] = '2024'
    audio['genre'] = 'Unknown'
    audio.save()

    # Add thumbnail
    audio = MP3(file_path, ID3=ID3)
    if track_info['thumbnail_url']:
        pic = requests.get(track_info['thumbnail_url']).content
        audio.tags.add(
            APIC(
                encoding=3,  # 3 is for utf-8
                mime='image/jpeg',  # image/jpeg or image/png
                type=3,  # 3 is for the cover image
                desc=u'Cover',
                data=pic
            )
        )
    audio.save()

# Telegram bot token ve kanal ID'si
TELEGRAM_API_ID = 6
TELEGRAM_API_HASH = 'eb06d4abfb49dc3eeb1aeb98ae0f581e'
TELEGRAM_BOT_TOKEN = ''
CHANNEL_ID = -1002239052069

app = Client("spotify_bot", api_id=TELEGRAM_API_ID, api_hash=TELEGRAM_API_HASH, bot_token=TELEGRAM_BOT_TOKEN)

async def send_song_info_to_channel(track_info):
    keyboard = [
        [InlineKeyboardButton("Listen on Spotify", url=track_info['track_link']),
         InlineKeyboardButton("Artist on Spotify", url=track_info['artist_link'])]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await app.send_photo(chat_id=CHANNEL_ID, photo=track_info['thumbnail_url'],
                                   caption=f"🎵 {track_info['track_name']} by {track_info['artist_name']}",
                                   reply_markup=reply_markup)
    await app.pin_chat_message(chat_id=CHANNEL_ID, message_id=message.message_id)
    return message.message_id

async def update_pinned_message(message_id, track_info):
    keyboard = [
        [InlineKeyboardButton("Listen on Spotify", url=track_info['track_link']),
         InlineKeyboardButton("Artist on Spotify", url=track_info['artist_link'])]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await app.edit_message_caption(chat_id=CHANNEL_ID, message_id=message_id,
                                       caption=f"🎵 {track_info['track_name']} by {track_info['artist_name']}",
                                       reply_markup=reply_markup)
        await asyncio.sleep(0.5)
        await app.edit_message_media(chat_id=CHANNEL_ID, message_id=message_id,
                                     media=track_info['thumbnail_url'])
    except Exception as e:
        print(f"Failed to update message: {e}")

async def send_song_to_channel(file_path):
    file_size = os.path.getsize(file_path)
    if file_size > 50 * 1024 * 1024:
        print(f"File size exceeds Telegram's limit: {file_size} bytes")
        return
    with open(file_path, 'rb') as audio:
        await app.send_audio(chat_id=CHANNEL_ID, audio=audio)

async def main():
    last_track = None
    pinned_message_id = None

    while True:
        current_track = get_current_track()
        if current_track:
            if current_track != last_track:
                print(f"Currently playing: {current_track['track_name']} by {current_track['artist_name']}")
                if pinned_message_id:
                    await update_pinned_message(pinned_message_id, current_track)
                else:
                    pinned_message_id = await send_song_info_to_channel(current_track)
                last_track = current_track
                downloaded_file = download_song(current_track['track_name'])
                if downloaded_file and os.path.exists(downloaded_file):
                    add_metadata(downloaded_file, current_track)
                    await send_song_to_channel(downloaded_file)
                else:
                    print(f"File not found: {downloaded_file}")
            else:
                print("Same track is still playing.")
        else:
            print("No track is currently playing.")
        await asyncio.sleep(20)  # 20 saniye bekle

if __name__ == "__main__":
    app.start()
    try:
        asyncio.run(main())
    finally:
        app.stop()
