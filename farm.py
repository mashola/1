import asyncio
import random
import os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# --- GITHUB SECRETS ---
PROXY_USER = os.getenv('PROXY_USER')
PROXY_PASS = os.getenv('PROXY_PASS')
ALBUM_LINKS_RAW = os.getenv('ALBUM_LINKS')
ALBUM_LINKS = ALBUM_LINKS_RAW.split(',') if ALBUM_LINKS_RAW else []

# Port 8000 is generally more stable for Webshare backbone
PROXY_SERVER = "http://p.webshare.io:8000"

async def run_viewer(playwright, id):
    device_name = random.choice(["Pixel 5", "iPhone 12", "Galaxy S8"])
    device = playwright.devices[device_name]
    
    # Launch with slightly more robust args
    browser = await playwright.chromium.launch(headless=True, args=[
        "--mute-audio",
        "--disable-setuid-sandbox",
        "--no-sandbox"
    ])
    
    try:
        # Added ignore_https_errors to bypass proxy handshake stalls
        context = await browser.new_context(
            **device,
            proxy={"server": PROXY_SERVER, "username": PROXY_USER, "password": PROXY_PASS},
            ignore_https_errors=True 
        )
        
        stealth = Stealth()
        await stealth.apply_stealth_async(context)
        page = await context.new_page()

        await page.route("**/*.{png,jpg,jpeg,css,woff2}", lambda route: route.abort())

        url = random.choice(ALBUM_LINKS)
        print(f"Viewer {id}: Starting {device_name} session...")
        
        # Increased timeout to 90s for slow proxy connections
        await page.goto(url, wait_until="commit", timeout=120000)
        await asyncio.sleep(15)
        
        # Tap Play
        play_btn = page.locator('button[aria-label="Play"], .play-btn, .icon-play, [data-testid="play-button"]').first
        await play_btn.wait_for(state="visible", timeout=30000)
        await play_btn.tap()
        
        print(f"Viewer {id}: SUCCESS. Playing track.")
        await asyncio.sleep(2700) 
        
    except Exception as e:
        print(f"Viewer {id}: Connection Error - {e}")
    finally:
        await browser.close()

async def main():
    if not ALBUM_LINKS or not PROXY_USER:
        print("CRITICAL: Secrets missing!")
        return

    async with async_playwright() as p:
        # NEW: Sequential launch to avoid "Tunnel" crashes
        for i in range(15):
            asyncio.create_task(run_viewer(p, i))
            await asyncio.sleep(8) # Wait 8 seconds between each bot start
        
        # Keep main loop alive for the duration of the cycle
        await asyncio.sleep(3300)

if __name__ == "__main__":
    asyncio.run(main())
