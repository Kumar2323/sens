import os
import re
import asyncio
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyppeteer import launch

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
    mp3_links = await find_links(url)
    
    if not mp3_links:
        await client.send_message(chat_id=message.chat.id, text="No MP3 links found.")
        return

    for link in mp3_links:
        filename = os.path.basename(link)
        cleaned_filename = await clean_file_name(filename)
        filepath = await download_file(link, filename)
        file_size = os.path.getsize(filepath) / (1024 * 1024)
        caption = f"File: {cleaned_filename}\nSize: {file_size:.2f} MB\nJoin @Naaflix_1"

        async with app:
            await client.send_audio(chat_id=CHANNEL_ID_1, audio=filepath, caption=caption)
            await client.send_audio(chat_id=CHANNEL_ID_2, audio=filepath, caption=caption)

        os.remove(filepath)

async def find_links(url):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url)
    content = await page.content()
    await browser.close()

    soup = BeautifulSoup(content, 'html.parser')
    mp3_links = []

    for link in soup.find_all('a'):
        href = link.get('href')
        if href.endswith('.mp3'):
            mp3_links.append(href)

    return mp3_links

async def clean_file_name(filename):
    cleaned_name = re.sub(r'[0-9]', '', filename)
    cleaned_name = re.sub(r'[^a-zA-Z\s.]', ' ', cleaned_name)
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name)
    return cleaned_name.strip()

async def download_file(url, filename):
    # Download the file using requests or another library
    pass

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
