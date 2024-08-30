import os
import re
import requests
import logging
import asyncio
from aiohttp import web
from bs4 import BeautifulSoup
from pyrogram import Client, filters

# Set up logging
logging.basicConfig(level=logging.INFO)

# Replace with your API details
API_HASH = os.environ.get('API_HASH')
API_ID = int(os.environ.get('API_ID'))
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Replace with your channel IDs
CHANNEL_ID_1 = int(os.environ.get('CHANNEL_ID_1'))
CHANNEL_ID_2 = int(os.environ.get('CHANNEL_ID_2'))

# Create a downloads directory if it doesn't exist
if not os.path.exists('downloads'):
    os.makedirs('downloads')

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("Send me a website URL to scan for MP3 links.")

@app.on_message(filters.text & ~filters.command("start"))
async def scan_website(client, message):
    url = message.text
    logging.info(f"Scanning URL: {url}")
    
    internal_links, external_links, mp3_links = await find_links(url)
    
    logging.info(f"Found {len(mp3_links)} MP3 links on {url}.")
    
    if not mp3_links:
        await client.send_message(chat_id=message.chat.id, text="No MP3 links found.")
        return

    for link in mp3_links:
        filename = os.path.basename(link)
        filename = filename.replace("sensongsmp", "").replace("sensongsmp3.com", "")
        cleaned_filename = await clean_file_name(filename)
        cleaned_filename = cleaned_filename.replace(" mp", "")
        cleaned_filename = cleaned_filename.replace(".", " ") + " mp3"
        cleaned_filename = cleaned_filename.replace(" mp mp3", " mp3")
        filepath = await download_file(link, filename)
        file_size = os.path.getsize(filepath) / (1024 * 1024)
        caption = f"File: {cleaned_filename}\nSize: {file_size:.2f} MB\nJoin @Naaflix_1"

        async with app:
            await client.send_audio(chat_id=CHANNEL_ID_1, audio=filepath, caption=caption)
            await client.send_audio(chat_id=CHANNEL_ID_2, audio=filepath, caption=caption)

        os.remove(filepath)

    await client.send_message(chat_id=message.chat.id, text=f"Found {len(internal_links)} internal links and {len(external_links)} external links on {url}.")

async def find_links(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    logging.info(f"Response status code: {response.status_code}")
    if response.status_code != 200:
        logging.error(f"Failed to retrieve URL: {url}")
        return [], [], []

    soup = BeautifulSoup(response.text, 'html.parser')
    internal_links = []
    external_links = []
    mp3_links = []

    for link in soup.find_all('a'):
        href = link.get('href')
        if href.startswith('/'):
            internal_links.append(url + href)
        elif href.startswith('http'):
            external_links.append(href)
        if href.endswith('.mp3'):
            mp3_links.append(href)

    return internal_links, external_links, mp3_links

async def clean_file_name(filename):
    cleaned_name = re.sub(r'[0-9]', '', filename)
    cleaned_name = re.sub(r'[^a-zA-Z\s.]', ' ', cleaned_name)
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name)
    return cleaned_name.strip()

async def download_file(url, filename):
    response = requests.get(url, stream=True)
    filepath = os.path.join('downloads', filename)
    with open(filepath, 'wb') as file:
        for chunk in response.iter_content(chunk_size=1024):
            file.write(chunk)
    return filepath

async def handle(request):
    return web.Response(text="Bot is running")

async def web_server():
    web_app = web.Application()
    web_app.router.add_get("/", handle)
    return web_app

async def main():
    await app.start()

    # Start web server
    port = int(os.environ.get("PORT", 8080))
    web_app = await web_server()
    web_runner = web.AppRunner(web_app)
    await web_runner.setup()
    site = web.TCPSite(web_runner, "0.0.0.0", port)
    await site.start()

    print("Bot started")
    await asyncio.Future()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        loop.run_until_complete(app.stop())
        loop.close()
