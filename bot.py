from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
import requests

# ===== CONFIG =====
API_ID = 22529712
API_HASH = "bce910690a1a50a2b72374b3efa4a980"
BOT_TOKEN = "8526713983:AAHYyRNWcN916FDp6e5NAEK8dUAq7gmwlbw"

app = Client("yt_mp3_thumb_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ===== START =====
@app.on_message(filters.command("start"))
def start(client, message):
    message.reply_text(
        "👋 **YouTube Downloader Bot**\n\n"
        "🔗 YouTube link bhejo\n"
        "🎵 MP3 ya 🖼 Thumbnail download karo"
    )

# ===== HANDLE LINK =====
@app.on_message(filters.text & filters.private)
def handle_link(client, message):
    url = message.text.strip()
    msg = message.reply_text("🔍 Processing link...")

    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)

        title = info.get("title", "No Title")
        thumb = info.get("thumbnail")

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎧 Download MP3", callback_data=f"mp3|{url}")],
            [InlineKeyboardButton("🖼 Download Thumbnail", callback_data=f"thumb|{url}")]
        ])

        client.send_photo(
            chat_id=message.chat.id,
            photo=thumb,
            caption=f"🎬 **{title}**\n\nChoose an option:",
            reply_markup=buttons
        )
        msg.delete()

    except Exception as e:
        msg.edit_text(f"❌ Error: {e}")

# ===== CALLBACK HANDLER =====
@app.on_callback_query()
def callbacks(client, callback):
    data = callback.data

    if data.startswith("mp3|"):
        url = data.split("|", 1)[1]
        callback.message.edit_caption("⏳ Downloading MP3...")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_file = os.path.splitext(filename)[0] + ".mp3"

        client.send_audio(
            chat_id=callback.message.chat.id,
            audio=mp3_file,
            title=info.get("title", "Song")
        )

        os.remove(mp3_file)
        callback.message.delete()

    elif data.startswith("thumb|"):
        url = data.split("|", 1)[1]

        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("720p", callback_data=f"thumb720|{url}"),
                InlineKeyboardButton("1080p", callback_data=f"thumb1080|{url}")
            ]
        ])

        callback.message.edit_caption(
            "🖼 Choose thumbnail quality:",
            reply_markup=buttons
        )

    elif data.startswith("thumb720|") or data.startswith("thumb1080|"):
        parts = data.split("|", 1)
        quality = parts[0]
        url = parts[1]

        callback.message.edit_caption("⏳ Downloading thumbnail...")

        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)

        thumb_url = info.get("thumbnail")
        title = info.get("title", "thumbnail")

        img_data = requests.get(thumb_url).content
        filename = f"{title}_thumbnail.jpg"

        with open(filename, "wb") as f:
            f.write(img_data)

        client.send_photo(
            chat_id=callback.message.chat.id,
            photo=filename,
            caption=f"🖼 **Thumbnail ({'720p' if '720' in quality else '1080p'})**"
        )

        os.remove(filename)
        callback.message.delete()

# ===== RUN =====
print("Bot is running...")
app.run()
