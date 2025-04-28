import urllib.parse
import pandas as pd
import requests
from config import AUTH_URL
import re
from playwright.sync_api import Playwright, sync_playwright, expect

apiKey = '5b0b5830-a3ed-4083-a6e3-c356b3d1e34e'
secretKey = '6v0pqbcvp5'
redirectUrl = 'https://127.0.0.1:5000/'
rurl = urllib.parse.quote('https://127.0.0.1:5000/',safe="")

uri = f'https://api-v2.upstox.com/login/authorization/dialog?response_type=code&client_id={apiKey}&redirect_uri={rurl}'
url = 'https://api-v2.upstox.com/login/authorization/token'
print(uri)
code = 'AfMmNC'
headers = {
    'accept': 'application/json',
    'Api-Version': '2.0',
    'Content-Type': 'application/x-www-form-urlencoded'
}

data = {
    'code': code,
    'client_id': apiKey,
    'client_secret': secretKey,
    'redirect_uri': redirectUrl,
    'grant_type': 'authorization_code'
}

response = requests.post(url, headers=headers, data=data)
json_response = response.json()

access_token = json_response['access_token']
print(access_token)
# def run(playwright: Playwright) -> None:
#     browser = playwright.chromium.launch(headless=True)
#     context = browser.new_context()
#     page = context.new_page()
#     with page.expect_request(f"*{rurl}?code*") as request:
#         page.goto(AUTH_URL)
#         page.locator("#mobileNum").fill("9351494734")
#         page.get_by_role("button", name="Get OTP").click()
#         page.locator("#otpNum").fill("542-682")
#         page.get_by_role("button", name="Continue").click()
#         page.get_by_role("textbox", name="Enter 6-digit PIN").fill("936142")
#         page.get_by_role("button", name="Continue").click()
#     # ---------------------
#     context.close()
#     browser.close()


# with sync_playwright() as playwright:
#     run(playwright) 

import requests

url = "https://api.upstox.com/v2/market-quote/quotes"



response = requests.request("GET", url, headers=headers, data=data)

print(response.text)