import os
import time
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

def main():
    server = HTTPServer(('127.0.0.1', 8896), QuietHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Mobile viewport matching user's phone screenshot
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto("http://127.0.0.1:8896/products.html", wait_until="networkidle")
        time.sleep(1.5)

        # Force loader hidden if needed
        page.evaluate("""() => {
            const loader = document.getElementById('site-loader');
            if (loader) loader.style.display = 'none';
            document.body.classList.add('site-loaded');
        }""")

        rescue_card = page.locator('.club-card[data-type="rescue"]')
        rescue_card.scroll_into_view_if_needed()
        time.sleep(0.5)

        shot_path = os.path.join(ARTIFACT_DIR, "rescue_mobile_after.png")
        page.screenshot(path=shot_path)
        print(f"Screenshot saved to {shot_path}")
        browser.close()

if __name__ == "__main__":
    main()
