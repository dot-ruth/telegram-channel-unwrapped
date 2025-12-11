from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("--- Telegram Session Generator ---")
print("Get your API_ID and API_HASH from https://my.telegram.org")

API_ID = int(input("Enter API_ID: "))
API_HASH = input("Enter API_HASH: ")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("\n👇 COPY THE STRING BELOW 👇\n")
    print(client.session.save())
    print("\n👆 COPY THE STRING ABOVE 👆\n")
    print("Paste this string into your .env file as SESSION_STRING")