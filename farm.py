import asyncio
import random
import os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# --- THIS PULLS YOUR SECRETS FROM GITHUB ---
PROXY_USER = os.getenv('PROXY_USER')
PROXY_PASS = os.getenv('PROXY_PASS')
# We expect a comma-separated list of links in the 'ALBUM_LINKS' secret
ALBUM_LINKS = os.getenv('ALBUM_LINKS').split(',') 

PROXY_SERVER = "http://p.webshare.io:80"

async def run_viewer(playwright, id):
    device_name = random.choice(["Pixel 5", "iPhone 12", "Galaxy S8"])
    device = playwright.devices[device_name]
    
    browser = await playwright.chromium.launch(headless=True, args=["--mute-audio"])
    
    # Secure context using your Secrets
    context = await browser.new_context(
        **device,
        proxy={"server": PROXY_SERVER, "username": PROXY_USER, "password": PROXY_PASS},
        is_mobile=True,
        has_touch=True
    )
    
    stealth = Stealth()
    await stealth.apply_stealth_async(context)
    page = await context.new_page()

    # Block heavy assets to speed up the GitHub Runner
    await page.route("**/*.{png,jpg,jpeg,css,woff2}", lambda route: route.abort())

    try:
        url = random.choice(ALBUM_LINKS)
        print(f"Viewer {id}: Starting {device_name} session...")
        await page.goto(url, wait_until="commit", timeout=90000)
        
        await asyncio.sleep(15)
        # Taps play on YouTube Music, Audiomack, or Boomplay
        await page.locator('button[aria-label="Play"], .play-btn, .icon-play').first.tap()
        
        print(f"Viewer {id}: Playing successfully.")
        await asyncio.sleep(2800) # Play for ~45 mins
    except Exception as e:
        print(f"Viewer {id}: Error - {e}")
    finally:
        await browser.close()

async def main():
    async with async_playwright() as p:
        # Launching 15-20 bots is safe for GitHub's 16GB RAM
        tasks = [run_viewer(p, i) for i in range(15)]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
