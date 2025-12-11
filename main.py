import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from src.config import BOT_TOKEN
from src.client import client
from src.bot import start, help_command, handle_input

async def main():
    print("Starting Telethon Client...")
    await client.start()
    
    print("Starting Bot API...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    
    await app.initialize()
    await app.start()
    
    print("Bot is running and listening!")
    await app.updater.start_polling()
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())