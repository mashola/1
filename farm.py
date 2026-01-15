import asyncio
import random
import os
import sys
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

print("--- SCRIPT STARTING: INITIALIZING ENGINE ---", flush=True)

PROXY_USER = os.getenv('PROXY_USER')
PROXY_PASS = os.getenv('PROXY_PASS')
ALBUM_LINKS_RAW = os.getenv('ALBUM_LINKS')

if not ALBUM_LINKS_RAW:
    print("CRITICAL ERROR: ALBUM_LINKS secret is empty!", flush=True)
    sys.exit(1)

ALBUM_LINKS = [link.strip() for link in ALBUM_LINKS_RAW.split(',')]

# Reverted to HTTP for authentication support, using standard Backbone Port
PROXY_SERVER = "http://p.webshare.io:80"

async def run_viewer(playwright, id):
    print(f"Viewer {id}: Booting...", flush=True)
    device = playwright.devices[random.choice(["Pixel 5", "iPhone 12", "Galaxy S8"])]
    
    browser = await playwright.chromium.launch(headless=True, args=[
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--mute-audio"
    ])
    
    try:
        context = await browser.new_context(
            **device,
            # HTTP supports Username/Password authentication perfectly
            proxy={
                "server": PROXY_SERVER, 
                "username": PROXY_USER, 
                "password": PROXY_PASS
            },
            ignore_https_errors=True
        )
        
        stealth = Stealth()
        await stealth.apply_stealth_async(context)
        page = await context.new_page()

        # Block images/css to save bandwidth
        await page.route("**/*.{png,jpg,jpeg,css,woff2}", lambda route: route.abort())

        url = random.choice(ALBUM_LINKS)
        print(f"Viewer {id}: Handshake Success. Loading {url}", flush=True)
        
        await page.goto(url, wait_until="commit", timeout=120000)
        await asyncio.sleep(20)
        
        # Universal Play Tap
        play_btn = page.locator('button[aria-label="Play"], .play-btn, .icon-play, [data-testid="play-button"]').first
        await play_btn.wait_for(state="visible", timeout=30000)
        await play_btn.tap()
        
        print(f"Viewer {id}: STREAM ACTIVE.", flush=True)
        await asyncio.sleep(2600) 
        
    except Exception as e:
        print(f"Viewer {id}: Connection Failed -> {e}", flush=True)
    finally:
        await browser.close()

async def main():
    print(f"Launching batch for {len(ALBUM_LINKS)} links...", flush=True)
    async with async_playwright() as p:
        # Launch 10 viewers
        for i in range(10): 
            asyncio.create_task(run_viewer(p, i))
            await asyncio.sleep(25) 
        
        await asyncio.sleep(3200)

if __name__ == "__main__":
    asyncio.run(main())
