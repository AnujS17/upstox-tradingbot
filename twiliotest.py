# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = "AC85917219bc00c74b41381a59e77d8e3e "
auth_token = "1f20e5b875eba4dd342c5aee2b66ca0f"
client = Client(account_sid, auth_token)

message = client.messages.create(
    to="+17822222917",
    from_="+919351494734",
    body="Hello from Python!")

print(message.sid)
    