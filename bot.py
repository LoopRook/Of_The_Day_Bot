# =========================================================
# Discord Quote of the Day Bot 
# All scheduled times are in US/Eastern (EST). Configure accordingly.
# Now fully configurable via environment variables (.env or Railway Variables UI)
#
# Features:
#  - Daily server rename & icon from quotes/images (optional, time settable)
#  - Daily song post from music channel to general (optional, time settable, links only)
#  - All features, times, and IDs can be set externally; no code edits required
# =========================================================

import discord
import random
import asyncio
import datetime
import pytz
import aiohttp
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import logging
import os

# ================ ENVIRONMENT CONFIG (RAILWAY/.env) ================
# Token and server/channel IDs
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID', '0'))
QUOTE_CHANNEL_ID = int(os.getenv('QUOTE_CHANNEL_ID', '0'))
ICON_CHANNEL_ID = int(os.getenv('ICON_CHANNEL_ID', '0'))
POST_CHANNEL_ID = int(os.getenv('POST_CHANNEL_ID', '0'))
MUSIC_CHANNEL_ID = int(os.getenv('MUSIC_CHANNEL_ID', '0'))
SONG_POST_CHANNEL_ID = int(os.getenv('SONG_POST_CHANNEL_ID', '0'))

# Feature toggles (enable/disable)
ENABLE_DAILY_QUOTE = os.getenv('ENABLE_DAILY_QUOTE', 'true').lower() == 'true'
ENABLE_DAILY_SONG = os.getenv('ENABLE_DAILY_SONG', 'true').lower() == 'true'

# Schedule times (in HH:MM, EST)
QUOTE_TIME = os.getenv('QUOTE_TIME', '4:00')  # 4:00 AM EST
SONG_TIME = os.getenv('SONG_TIME', '10:00')   # 10:00 AM EST

# ================ DISCORD BOT INITIALIZATION ================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
client = discord.Client(intents=intents)

logging.basicConfig(level=logging.INFO)
logging.getLogger('discord.gateway').setLevel(logging.WARNING)

used_icon_message_ids = set()

# =========================================================
# UTILITY FUNCTIONS (Time, Fonts, etc.)
# =========================================================
def seconds_until_time_str(timestr):
    """
    Return seconds until next given time (e.g. '4:00'), in EST.
    """
    hour, minute = [int(x) for x in timestr.strip().split(":")]
    tz = pytz.timezone('US/Eastern')
    now = datetime.datetime.now(tz)
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if now >= next_run:
        next_run += datetime.timedelta(days=1)
    return (next_run - now).total_seconds()

def truncate_to_100_chars(text):
    return text if len(text) <= 100 else text[:97].rsplit(' ', 1)[0] + '...'

def load_fonts(size):
    fonts = []
    paths = ["DejaVuSans-Bold.ttf", "NotoSansKR-Bold.ttf", "NotoSansSymbols-Bold.ttf"]
    for path in paths:
        try:
            font = ImageFont.truetype(path, size)
            fonts.append(font)
        except Exception as e:
            print(f"❌ Failed to load font '{path}': {e}")
            fonts.append(None)
    return fonts

def can_render_all(text, font, name):
    try:
        for char in text:
            if char == ' ':
                continue
            if not font.getmask(char).getbbox():
                print(f"❌ Font '{name}' cannot render '{char}' (U+{ord(char):04X})")
                return False
        print(f"✅ Font '{name}' supports full string: \"{text}\"")
        return True
    except Exception as e:
        print(f"❌ Exception checking '{name}': {e}")
        return False

def choose_font(text, fonts, names):
    for font, name in zip(fonts, names):
        if font and can_render_all(text, font, name):
            return font
    return fonts[0]  # Fallback

# =========================================================
# FEATURE 1: DAILY SERVER RENAME & ICON (QUOTE OF THE DAY)
# =========================================================
async def generate_card(server_name, quote_user, icon_user, icon_bytes):
    try:
        base = Image.new("RGBA", (800, 450), (0, 0, 0, 255))
        icon = Image.open(BytesIO(icon_bytes)).convert("RGBA").resize((400, 400))
        blurred_bg = icon.resize((800, 450)).filter(ImageFilter.GaussianBlur(12))
        base.paste(blurred_bg, (0, 0))

        mask = Image.new("L", (400, 400), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, 400, 400), radius=40, fill=255)
        icon.putalpha(mask)
        base.paste(icon, (25, 25), icon)

        draw = ImageDraw.Draw(base)
        title_fonts = load_fonts(36)
        meta_fonts = load_fonts(24)
        font_names = ["NotoSansKR", "NotoSansSymbols", "DejaVuSans"]

        words, line, lines = server_name.split(), "", []
        for word in words:
            test = f"{line} {word}".strip()
            font = choose_font(test, title_fonts, font_names) or title_fonts[0]
            if draw.textlength(test, font=font) < 300:
                line = test
            else:
                lines.append(line)
                line = word
        lines.append(line)

        y_text = 80
        for line in lines:
            font = choose_font(line, title_fonts, font_names) or title_fonts[0]
            draw.text((450, y_text), line, font=font, fill=(255, 255, 255))
            y_text += 40

        def render_meta(label, name, offset):
            font = choose_font(name, meta_fonts, font_names)
            if not font or not can_render_all(name, font, label):
                print(f"⚠️ Fallback: {label} '{name}' has unsupported glyphs, using 'Unknown'")
                name = "Unknown"
                font = meta_fonts[0]
            color = (200, 200, 200) if label == "Quote by" else (180, 180, 180)
            draw.text((450, offset), f"{label}: {name}", font=font, fill=color)

        render_meta("Quote by", quote_user, y_text + 10)
        render_meta("Icon by", icon_user, y_text + 50)

        buffer = BytesIO()
        base.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        return None

async def get_random_quote(channel):
    all_lines = []
    async for message in channel.history(limit=None, oldest_first=False):
        if message.author.bot:
            continue
        lines = message.content.strip().splitlines()
        all_lines.extend([(line, message.author.display_name) for line in lines if line.strip()])
    return random.choice(all_lines) if all_lines else (None, None)

async def get_random_icon(channel):
    all_images = []
    async for message in channel.history(limit=None, oldest_first=False):
        if message.author.bot:
            continue
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith("image"):
                all_images.append((attachment.url, message.author.display_name))
    return random.choice(all_images) if all_images else (None, None)

async def process_rename(channel, echo=True):
    try:
        guild = client.get_guild(GUILD_ID)
        quote_channel = client.get_channel(QUOTE_CHANNEL_ID)
        icon_channel = client.get_channel(ICON_CHANNEL_ID)

        quote, quote_user = await get_random_quote(quote_channel)
        image_url, icon_user = await get_random_icon(icon_channel)

        if not quote:
            print("⚠️ No valid quote found.")
            return
        if not image_url:
            print("⚠️ No valid image found.")
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                icon_bytes = await resp.read()

        await guild.edit(name=truncate_to_100_chars(quote), icon=icon_bytes)
        print(f"📝 Server renamed to: \"{quote}\"")

        image_file = await generate_card(quote, quote_user or "Unknown", icon_user or "Unknown", icon_bytes)
        if image_file:
            image_file.seek(0)
            await channel.send(file=discord.File(fp=image_file, filename="update.png"))
            if channel.id != POST_CHANNEL_ID:
                image_file.seek(0)
                post_channel = client.get_channel(POST_CHANNEL_ID)
                await post_channel.send(file=discord.File(fp=image_file, filename="update.png"))
    except Exception as e:
        print(f"❌ Rename process failed: {e}")

async def schedule_rename():
    await client.wait_until_ready()
    while not client.is_closed():
        wait_time = seconds_until_time_str(QUOTE_TIME)
        print(f"⏰ Sleeping for {wait_time/3600:.2f} hours until Quote of the Day ({QUOTE_TIME} EST)")
        await asyncio.sleep(wait_time)
        channel = client.get_channel(QUOTE_CHANNEL_ID)
        await process_rename(channel)

# =========================================================
# FEATURE 2: DAILY SONG POST
# =========================================================
MUSIC_URL_PATTERNS = [
    r"(https?://)?(www\.)?(youtube\.com|youtu\.be|soundcloud\.com|spotify\.com)/[^\s]+"
]

def is_music_link(line):
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in MUSIC_URL_PATTERNS)

async def get_random_song(channel):
    all_links = []
    async for message in channel.history(limit=None, oldest_first=False):
        if message.author.bot:
            continue
        lines = message.content.strip().splitlines()
        for line in lines:
            if line.strip() and is_music_link(line.strip()):
                all_links.append((line.strip(), message.author.display_name))
    return random.choice(all_links) if all_links else (None, None)

is_song_searching = False

async def process_daily_song():
    global is_song_searching
    if is_song_searching:
        print("⚠️ Song search already in progress. Skipping new request.")
        post_channel = client.get_channel(SONG_POST_CHANNEL_ID)
        if post_channel:
            await post_channel.send("⚠️ Song search is already running. Please wait for it to finish.")
        return
    is_song_searching = True
    try:
        print("DEBUG: Entered process_daily_song()")
        music_channel = client.get_channel(MUSIC_CHANNEL_ID)
        post_channel = client.get_channel(SONG_POST_CHANNEL_ID)
        print(f"DEBUG: music_channel={music_channel}, post_channel={post_channel}")
        if not music_channel:
            print("❌ Music channel not found.")
            is_song_searching = False
            return
        if not post_channel:
            print("❌ Song post channel not found.")
            is_song_searching = False
            return
        song, user = await get_random_song(music_channel)
        print(f"DEBUG: Song={song}, User={user}")
        if not song:
            print("⚠️ No valid music link found in music channel.")
            await post_channel.send("⚠️ No valid music link found in music channel.")
            is_song_searching = False
            return
        await post_channel.send(f"""🎵 **Song of the Day** (from {user}):\n{song}""")
        print(f"🎵 Posted song of the day: {song}")
    except Exception as e:
        print(f"❌ Song post failed: {e}")
    finally:
        is_song_searching = False

async def schedule_daily_song():
    await client.wait_until_ready()
    while not client.is_closed():
        wait_time = seconds_until_time_str(SONG_TIME)
        print(f"⏰ Sleeping for {wait_time/3600:.2f} hours until Song of the Day ({SONG_TIME} EST)")
        await asyncio.sleep(wait_time)
        await process_daily_song()

# =========================================================
# DISCORD BOT EVENTS (STARTUP, COMMANDS)
# =========================================================
@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    # Start scheduled features if enabled
    if ENABLE_DAILY_QUOTE:
        client.loop.create_task(schedule_rename())
    if ENABLE_DAILY_SONG:
        client.loop.create_task(schedule_daily_song())

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.lower().startswith("!rename"):
        await process_rename(message.channel)
    if message.content.lower().startswith("!song"):
        await process_daily_song()

# =========================================================
# BOT ENTRYPOINT
# =========================================================
client.run(TOKEN)
