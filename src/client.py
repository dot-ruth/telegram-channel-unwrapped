from telethon import TelegramClient
from telethon.sessions import StringSession
from src.config import API_ID, API_HASH, SESSION_STRING

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)