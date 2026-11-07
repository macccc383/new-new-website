import os
import sys
import time
import subprocess
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

ROOT_DIR = r"c:\Users\hello\Downloads\new-new-website-main\new-new-website-main"
ARTIFACT_DIR = r"C:\Users\hello\.gemini\antigravity\brain\8762d76b-a756-47bf-b386-c3e2e9041873"

class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT_DIR, **kwargs)
    def log_message(self, format, *args):
        pass

def run_server(server):
    server.serve_forever()

def main():
    server = HTTPServer(('127.0.0.1', 8899), QuietHandler)
    server_thread = threading.Thread(target=run_server, args=(server,), daemon=True)
    server_thread.start()
    print("Server running on http://127.0.0.1:8899")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 1. Desktop Test (Dark Theme)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        
        # Test navigation from contact.html
        print("Navigating to contact.html...")
        page.goto("http://127.0.0.1:8899/contact.html", wait_until="networkidle")
        time.sleep(1)
        
        # Click on Kentack Phuong Dong card
        print("Clicking Kentack Phuong Dong card...")
        card = page.locator(".location-card-clickable").first
        card.click()
        page.wait_for_url("**/kentack-phuong-dong.html", timeout=5000)
        print("Successfully navigated to:", page.url)
        time.sleep(1)

        # Verify Google Maps link
        maps_link = page.locator(".google-maps-link")
        href = maps_link.get_attribute("href")
        print("Google Maps link href:", href)
        assert href == "https://maps.app.goo.gl/ohDafiAU3E2ojwfu7", f"Unexpected href: {href}"

        # Capture dark theme screenshot
        dark_shot = os.path.join(ARTIFACT_DIR, "showroom_phuongdong_dark.png")
        page.screenshot(path=dark_shot, full_page=False)
        print(f"Saved dark theme screenshot to {dark_shot}")

        # Light theme test
        theme_btn = page.locator("#theme-toggle")
        theme_btn.click()
        time.sleep(0.5)
        light_shot = os.path.join(ARTIFACT_DIR, "showroom_phuongdong_light.png")
        page.screenshot(path=light_shot, full_page=False)
        print(f"Saved light theme screenshot to {light_shot}")

        # Test Lightbox opening
        first_bento_item = page.locator(".bento-item").first
        first_bento_item.click()
        time.sleep(0.5)
        modal = page.locator("#phuongdong-modal")
        assert "open" in modal.get_attribute("class"), "Lightbox modal not open!"
        counter = page.locator("#lightbox-counter").inner_text()
        print("Lightbox opened, counter text:", counter)
        
        # Click next in lightbox
        next_btn = page.locator(".lightbox-next")
        next_btn.click()
        time.sleep(0.3)
        counter2 = page.locator("#lightbox-counter").inner_text()
        print("After next button, counter text:", counter2)
        assert counter2 == "2 / 7", f"Expected 2 / 7 but got {counter2}"

        lightbox_shot = os.path.join(ARTIFACT_DIR, "showroom_lightbox.png")
        page.screenshot(path=lightbox_shot, full_page=False)
        print(f"Saved lightbox screenshot to {lightbox_shot}")

        # Close lightbox
        close_btn = page.locator(".gallery-modal-close")
        close_btn.click()
        time.sleep(0.5)
        page.close()

        # 2. Mobile Viewport Test (390x844)
        mobile_page = browser.new_page(viewport={"width": 390, "height": 844})
        mobile_page.goto("http://127.0.0.1:8899/kentack-phuong-dong.html", wait_until="networkidle")
        time.sleep(1)
        mobile_shot = os.path.join(ARTIFACT_DIR, "showroom_phuongdong_mobile.png")
        mobile_page.screenshot(path=mobile_shot, full_page=True)
        print(f"Saved mobile screenshot to {mobile_shot}")
        mobile_page.close()

        # 3. KH460 Test
        kh460_page = browser.new_page(viewport={"width": 1440, "height": 900})
        kh460_page.goto("http://127.0.0.1:8899/KH460/contact.html", wait_until="networkidle")
        time.sleep(1)
        kh460_card = kh460_page.locator(".location-card-clickable").first
        kh460_card.click()
        kh460_page.wait_for_url("**/KH460/kentack-phuong-dong.html", timeout=5000)
        print("KH460 navigation successful to:", kh460_page.url)
        time.sleep(1)
        kh460_shot = os.path.join(ARTIFACT_DIR, "showroom_kh460_dark.png")
        kh460_page.screenshot(path=kh460_shot, full_page=False)
        print(f"Saved KH460 screenshot to {kh460_shot}")
        kh460_page.close()

        browser.close()
        print("All tests completed successfully!")

if __name__ == "__main__":
    main()
