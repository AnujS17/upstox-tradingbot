from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.webkit.launch()
    page = browser.new_page()
    page.goto("https://playwright.dev/")
    page.screenshot(path="example.png")
    browser.close()

    'https://api-v2.upstox.com/login/authorization/dialog?response_type=code&client_id=5b0b5830-a3ed-4083-a6e3-c356b3d1e34e&redirect_uri=https%3A%2F%2F127.0.0.1%3A5000%2F'