import asyncio
from telethon.errors import FloodWaitError

def format_hour(h):
    suffix = "AM" if h < 12 else "PM"
    hour = h % 12
    hour = 12 if hour == 0 else hour
    return f"{hour} {suffix}"

async def safe_telethon_call(func, *args, **kwargs):
    """
    Wrap a Telethon call safely to handle FloodWaitError automatically.
    """
    while True:
        try:
            return await func(*args, **kwargs)
        except FloodWaitError as e:
            print(f"FloodWait: sleeping {e.seconds} seconds 😅")
            await asyncio.sleep(e.seconds)