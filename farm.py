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

PROXY_SERVER = "http://p.webshare.io:80"

async def run_viewer(playwright, id):
    # Randomly pick a mobile device identity
    device_name = random.choice(["Pixel 5", "iPhone 12", "Galaxy S8"])
    device = playwright.devices[device_name]
    
    # Launch browser per viewer for maximum stability
    browser = await playwright.chromium.launch(headless=True, args=["--mute-audio"])
    
    try:
        # FIXED: Removed duplicate 'is_mobile' and 'has_touch' because **device already has them
        context = await browser.new_context(
            **device,
            proxy={"server": PROXY_SERVER, "username": PROXY_USER, "password": PROXY_PASS}
        )
        
        stealth = Stealth()
        await stealth.apply_stealth_async(context)
        page = await context.new_page()

        # Block heavy assets to save bandwidth on GitHub Actions
        await page.route("**/*.{png,jpg,jpeg,css,woff2}", lambda route: route.abort())

        url = random.choice(ALBUM_LINKS)
        print(f"Viewer {id}: [{device_name}] Loading {url}")
        
        await page.goto(url, wait_until="commit", timeout=90000)
        await asyncio.sleep(15)
        
        # Universal Play Button: Taps the first play icon it finds
        play_btn = page.locator('button[aria-label="Play"], .play-btn, .icon-play, [data-testid="play-button"]').first
        await play_btn.wait_for(state="visible", timeout=30000)
        await play_btn.tap()
        
        print(f"Viewer {id}: SUCCESS. Stream is active.")
        # Play for 45 minutes
        await asyncio.sleep(2700) 
        
    except Exception as e:
        print(f"Viewer {id}: Encountered an error - {e}")
    finally:
        await browser.close()

async def main():
    if not ALBUM_LINKS or not PROXY_USER:
        print("CRITICAL ERROR: Secrets are missing or empty!")
        return

    async with async_playwright() as p:
        # Launching 15 viewers per hour is the "safe zone" for GitHub RAM
        tasks = [run_viewer(p, i) for i in range(15)]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
