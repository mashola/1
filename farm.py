import asyncio
import random
import os
import sys
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# HEARTBEAT: This tells you immediately if the script is alive
print("--- SCRIPT INITIALIZED: LOADING SECRETS ---", flush=True)

PROXY_USER = os.getenv('PROXY_USER')
PROXY_PASS = os.getenv('PROXY_PASS')
ALBUM_LINKS_RAW = os.getenv('ALBUM_LINKS')
ALBUM_LINKS = ALBUM_LINKS_RAW.split(',') if ALBUM_LINKS_RAW else []

# Webshare Backbone Port
PROXY_SERVER = "http://p.webshare.io:8000"

async def run_viewer(playwright, id):
    print(f"Viewer {id}: Booting...", flush=True)
    device = playwright.devices[random.choice(["Pixel 5", "iPhone 12"])]
    
    # Launch with extreme hardware efficiency
    browser = await playwright.chromium.launch(headless=True, args=[
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--mute-audio"
    ])
    
    try:
        context = await browser.new_context(
            **device,
            proxy={"server": PROXY_SERVER, "username": PROXY_USER, "password": PROXY_PASS},
            ignore_https_errors=True
        )
        
        stealth = Stealth()
        await stealth.apply_stealth_async(context)
        page = await context.new_page()

        # Block everything except the music player script
        await page.route("**/*.{png,jpg,jpeg,css,woff2}", lambda route: route.abort())

        url = random.choice(ALBUM_LINKS)
        print(f"Viewer {id}: Navigating to {url}", flush=True)
        
        # 'commit' is the fastest wait state
        await page.goto(url, wait_until="commit", timeout=90000)
        await asyncio.sleep(15)
        
        # Multi-platform Play Button Selector
        play_btn = page.locator('button[aria-label="Play"], .play-btn, .icon-play, [data-testid="play-button"]').first
        await play_btn.click(timeout=30000)
        
        print(f"Viewer {id}: STREAM STARTED SUCCESSFULLY.", flush=True)
        await asyncio.sleep(2600) 
        
    except Exception as e:
        print(f"Viewer {id}: Stopped due to -> {e}", flush=True)
    finally:
        await browser.close()

async def main():
    if not ALBUM_LINKS or not PROXY_USER:
        print("CRITICAL ERROR: ALBUM_LINKS or PROXY_USER is empty in GitHub Secrets!", flush=True)
        return

    print(f"Starting Farm with {len(ALBUM_LINKS)} target links...", flush=True)

    async with async_playwright() as p:
        # We launch them one by one with a delay to prevent GitHub CPU spikes
        for i in range(12): # Reduced to 12 for better stability
            asyncio.create_task(run_viewer(p, i))
            await asyncio.sleep(15) # Wait 15s between each bot
        
        # Total wait time to keep the Action alive
        await asyncio.sleep(3000)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
