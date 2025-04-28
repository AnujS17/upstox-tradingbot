# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client
from config import account_sid, auth_token

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = account_sid
auth_token = auth_token 
client = Client(account_sid, auth_token)

message = client.messages.create(
    to="+17822222917",
    from_="+919351494734",
    body="Hello from Python!")

print(message.sid)
    