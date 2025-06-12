from fastapi import FastAPI
from pydantic import BaseModel
from upstox_api.api import Upstox, TransactionType, OrderType, ProductType, DurationType, LiveFeedType
import uvicorn
import json
import os

app = FastAPI()

# === Fill these with your actual credentials ===
api_key = '5b0b5830-a3ed-4083-a6e3-c356b3d1e34e'
api_secret = '6v0pqbcvp5'
redirect_uri = 'https://127.0.0.1:5000/'  # Registered in Upstox dev portal
access_token = 'eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI3NEFMNVoiLCJqdGkiOiI2ODRhZDMzOGI4ZWRlMDAyODkyMzUwMjciLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzQ5NzM0MjAwLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NDk3NjU2MDB9.FiGupxajSUzJIxb4G_3ouYK__cE-7yArfn1aAlCbFlo'  # Set this after manual login flow

# === Initialize Upstox session ===
u = Upstox(api_key, api_secret)
u.set_access_token(access_token)

# === Pending order queue file ===
PENDING_FILE = "order_queue.json"
if not os.path.exists(PENDING_FILE):
    with open(PENDING_FILE, "w") as f:
        json.dump([], f)

# === Alert model ===
class Alert(BaseModel):
    action: str
    symbol: str  # e.g. "NSE:RELIANCE"
    qty: int = 0  # optional

# === Receive alert from TradingView ===
@app.post("/webhook")
async def receive_alert(alert: Alert):
    print(f"\n[ALERT RECEIVED] {alert.dict()}")
    with open(PENDING_FILE, "r+") as f:
        queue = json.load(f)
        queue.append(alert.dict())
        f.seek(0)
        json.dump(queue, f, indent=2)
    return {"message": "Trade alert received. Awaiting confirmation."}

# === View pending trades ===
@app.get("/pending-orders")
def view_pending():
    with open(PENDING_FILE, "r") as f:
        return json.load(f)

# === Execute a selected trade ===
@app.post("/execute")
def execute_order(index: int):
    with open(PENDING_FILE, "r+") as f:
        queue = json.load(f)
        if index >= len(queue):
            return {"error": "Invalid index"}
        order = queue.pop(index)
        f.seek(0)
        f.truncate()
        json.dump(queue, f, indent=2)

    try:
        exchange, symbol = order['symbol'].split(":")
        instrument = u.get_instrument_by_symbol(exchange, symbol)
        txn_type = TransactionType.Buy if order['action'].lower() == "buy" else TransactionType.Sell

        qty = order.get('qty', 0)
        if qty == 0:
            # Get LTP
            quote = u.get_live_feed(instrument, LiveFeedType.LTP)
            ltp = quote['ltp']

            # Get available funds
            funds = u.get_funds()
            available_cash = float(funds['available_margin']['equity'])

            qty = int(available_cash / ltp)
            if qty < 1:
                return {"error": "Insufficient funds to buy even 1 share"}

        # Place the order
        response = u.place_order(
            transaction_type=txn_type,
            instrument=instrument,
            quantity=qty,
            order_type=OrderType.Market,
            product=ProductType.Delivery,
            duration=DurationType.DAY
        )

        print(f"[ORDER EXECUTED] {txn_type} {qty} of {symbol}")
        return {
            "message": "Trade executed successfully",
            "symbol": symbol,
            "qty": qty,
            "order_id": response['data']['order_id']
        }

    except Exception as e:
        return {"error": str(e)}

# === Reject a selected trade ===
@app.post("/reject")
def reject_order(index: int):
    with open(PENDING_FILE, "r+") as f:
        queue = json.load(f)
        if index >= len(queue):
            return {"error": "Invalid index"}
        removed = queue.pop(index)
        f.seek(0)
        f.truncate()
        json.dump(queue, f, indent=2)
    return {"message": "Trade rejected", "rejected_order": removed}

# === Run the FastAPI app ===
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
