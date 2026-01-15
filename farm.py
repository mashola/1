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

# SWITCHED TO PORT 3128: More stable for GitHub Action Tunnels
PROXY_SERVER = "http://p.webshare.io:3128"

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
            proxy={"server": PROXY_SERVER, "username": PROXY_USER, "password": PROXY_PASS},
            ignore_https_errors=True
        )
        
        stealth = Stealth()
        await stealth.apply_stealth_async(context)
        page = await context.new_page()
        await page.route("**/*.{png,jpg,jpeg,css,woff2}", lambda route: route.abort())

        url = random.choice(ALBUM_LINKS)
        
        # --- ROBUST RETRY LOGIC FOR TUNNEL ---
        connected = False
        for attempt in range(3):
            try:
                print(f"Viewer {id}: Loading {url} (Attempt {attempt+1})", flush=True)
                # Reduced wait_until to 'commit' to stop the tunnel from timing out during heavy loads
                await page.goto(url, wait_until="commit", timeout=90000)
                connected = True
                break
            except Exception as e:
                print(f"Viewer {id}: Tunnel stalled. Retrying in 5s...", flush=True)
                await asyncio.sleep(5)
        
        if not connected:
            raise Exception("Persistent Tunnel Failure")

        # Play Logic
        await asyncio.sleep(15)
        play_btn = page.locator('button[aria-label="Play"], .play-btn, .icon-play, [data-testid="play-button"]').first
        await play_btn.wait_for(state="visible", timeout=20000)
        await play_btn.tap()
        
        print(f"Viewer {id}: SUCCESS. Stream is active.", flush=True)
        # Hold the stream for 45 mins
        await asyncio.sleep(2700) 
        
    except Exception as e:
        print(f"Viewer {id}: Connection Failed -> {e}", flush=True)
    finally:
        await browser.close()

async def main():
    print(f"Launching batch for {len(ALBUM_LINKS)} links...", flush=True)
    async with async_playwright() as p:
        # Launch 8 viewers (Lowering concurrency to reduce pressure on the proxy tunnel)
        for i in range(8): 
            asyncio.create_task(run_viewer(p, i))
            await asyncio.sleep(40) # 40s gap gives the tunnel time to stabilize
        
        await asyncio.sleep(3200)

if __name__ == "__main__":
    asyncio.run(main())
