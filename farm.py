import asyncio
import random
import os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# --- GITHUB SECRETS ---
PROXY_USER = os.getenv('PROXY_USER')
PROXY_PASS = os.getenv('PROXY_PASS')
ALBUM_LINKS = os.getenv('ALBUM_LINKS').split(',') if os.getenv('ALBUM_LINKS') else []

PROXY_SERVER = "http://p.webshare.io:80"

async def run_viewer(playwright, id):
    # Randomly pick a mobile device
    device_name = random.choice(["Pixel 5", "iPhone 12", "Galaxy S8"])
    device = playwright.devices[device_name]
    
    browser = await playwright.chromium.launch(headless=True, args=["--mute-audio"])
    
    try:
        # FIXED: Removed duplicate is_mobile/has_touch
        context = await browser.new_context(
            **device,
            proxy={"server": PROXY_SERVER, "username": PROXY_USER, "password": PROXY_PASS}
        )
        
        stealth = Stealth()
        await stealth.apply_stealth_async(context)
        page = await context.new_page()

        # Block images/css to save bandwidth on GitHub
        await page.route("**/*.{png,jpg,jpeg,css,woff2}", lambda route: route.abort())

        url = random.choice(ALBUM_LINKS)
        print(f"Viewer {id}: [{device_name}] Accessing {url}")
        
        await page.goto(url, wait_until="commit", timeout=60000)
        await asyncio.sleep(15)
        
        # Universal Play Button Tap
        await page.locator('button[aria-label="Play"], .play-btn, .icon-play, [data-testid="play-button"]').first.tap()
        
        print(f"Viewer {id}: Success. Listening...")
        # Play for 45 minutes
        await asyncio.sleep(2700) 
        
    except Exception as e:
        print(f"Viewer {id}: Failed - {e}")
    finally:
        await browser.close()

async def main():
    if not ALBUM_LINKS or not PROXY_USER:
        print("ERROR: Missing Secrets!")
        return

    async with async_playwright() as p:
        # Run 15 viewers per cycle
        tasks = [run_viewer(p, i) for i in range(15)]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
