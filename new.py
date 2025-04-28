import requests
import json
import upstox_client
from pprint import pprint
from upstox_client.rest import ApiException

profileUrl  = f"https://api.upstox.com/v2/market-quote/quotes"
accessToken = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI3NEFMNVoiLCJqdGkiOiI2N2VkYTY5Y2E4ZTMwMzUyMTRlMWIyMzciLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzQzNjI3OTMyLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NDM2MzEyMDB9.mcnCJnGv8cQvQJWulIzCjJPjFn9zIEKObBHVVYMEDoQ"

headers = {
    "accept": "application/json",
    "Api-Version": "2.0",
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization" : f"Bearer {accessToken}"
}

# configuration = upstox_client.Configuration()
# configuration.access_token = accessToken

# api_instance = upstox_client.MarketQuoteApi(upstox_client.ApiClient(configuration))
# symbol = 'REC' # str | Comma separated list of symbols
# api_version = 'V2' # str | API Version Header

#     # Market quotes and instruments - Full market quotes

# try:
#     # Market quotes and instruments - Full market quotes
#     api_response = api_instance.get_full_market_quote(symbol, api_version)
#     pprint(api_response)
# except ApiException as e:
#     print("Exception when calling MarketQuoteApi->get_full_market_quote: %s\n" % e)

url = 'https://api.upstox.com/v2/market-quote/ohlc'


data = {
    "instrument_key": "NSE_EQ|INE669E01016",
    "interval": "1d"
}

response = requests.get(url, headers=headers, params=data)

print(response.status_code)
print(response.json())