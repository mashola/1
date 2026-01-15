import asyncio
import random
import os
import sys
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# Forces logs to show up in GitHub Actions in real-time
print("--- SCRIPT STARTING: INITIALIZING ENGINE ---", flush=True)

# LOAD SECRETS
PROXY_USER = os.getenv('PROXY_USER')
PROXY_PASS = os.getenv('PROXY_PASS')
ALBUM_LINKS_RAW = os.getenv('ALBUM_LINKS')

if not ALBUM_LINKS_RAW:
    print("CRITICAL ERROR: ALBUM_LINKS secret is empty!", flush=True)
    sys.exit(1)

ALBUM_LINKS = [link.strip() for link in ALBUM_LINKS_RAW.split(',')]
PROXY_SERVER = "http://p.webshare.io:8000"

async def run_viewer(playwright, id):
    print(f"Viewer {id}: Booting browser instance...", flush=True)
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
            proxy={"server": PROXY_SERVER, "username": PROXY_USER, "password": PROXY_PASS},
            ignore_https_errors=True
        )
        
        stealth = Stealth()
        await stealth.apply_stealth_async(context)
        page = await context.new_page()

        # Save bandwidth on GitHub's network
        await page.route("**/*.{png,jpg,jpeg,css,woff2}", lambda route: route.abort())

        url = random.choice(ALBUM_LINKS)
        print(f"Viewer {id}: Navigating to {url}", flush=True)
        
        await page.goto(url, wait_until="commit", timeout=90000)
        await asyncio.sleep(15)
        
        # Universal Play Button: YT Music, Boomplay, Audiomack
        play_btn = page.locator('button[aria-label="Play"], .play-btn, .icon-play, [data-testid="play-button"]').first
        await play_btn.wait_for(state="visible", timeout=30000)
        await play_btn.tap()
        
        print(f"Viewer {id}: STREAM ACTIVE. Playing now.", flush=True)
        await asyncio.sleep(2600) 
        
    except Exception as e:
        print(f"Viewer {id}: Stopped -> {e}", flush=True)
    finally:
        await browser.close()

async def main():
    print(f"Found {len(ALBUM_LINKS)} target links. Launching batch...", flush=True)

    async with async_playwright() as p:
        # Pacing is critical to prevent "net::ERR_TUNNEL_CONNECTION_FAILED"
        for i in range(12): 
            asyncio.create_task(run_viewer(p, i))
            await asyncio.sleep(20) # 20s gap between each browser start
        
        # Keeps the runner alive for the 55-minute window
        await asyncio.sleep(3100)

if __name__ == "__main__":
    asyncio.run(main())
