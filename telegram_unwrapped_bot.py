import asyncio
import uuid
import telegram_client
import os
import json
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from telethon.errors import ChannelPrivateError, ChannelInvalidError
from generate_card import create_summary_card

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def fetch_messages_for_year(channel_identifier, session_id):
    year = datetime.now().year

    start_local = datetime(year, 1, 1, 0, 0, 0)
    start_utc = start_local.astimezone(timezone.utc)

    try:
        channel = await telegram_client.client.get_entity(channel_identifier)
        messages_out = []
        count = 0

        async for msg in telegram_client.client.iter_messages(channel, reverse=False):
            if msg.date < start_utc:
                break
            messages_out.append({
                "id": msg.id,
                "date": msg.date.isoformat(),
                "sender_id": getattr(msg.from_id, "user_id", None) if msg.from_id else None,
                "text": msg.message,
                "media": True if msg.media else False,
                "views": getattr(msg, "views", None),
                "forwards": getattr(msg, "forwards", None),
                "reactions": [r.to_dict() for r in msg.reactions.results] if getattr(msg, "reactions", None) else None
            })

            count += 1
            

        with open(f"{channel_identifier}-{session_id}.json", "w", encoding="utf-8") as f:
            json.dump({
                "channel": str(channel),
                "year": year,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "messages_count": len(messages_out),
                "messages": messages_out
            }, f, ensure_ascii=False, indent=2)

        return len(messages_out)

    except ChannelPrivateError:
        print("Error: Channel is private or you do not have access.")
        return 0
    except ChannelInvalidError:
        print("Error: Channel identifier invalid.")
        return 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! Welcome to Telegram Unwrapped Bot.\n\n"
        "Send me any channel username (e.g., @mychannel) and I’ll generate:\n"
        "• Your channel’s yearly summary\n"
        "• The top performing post of the year\n"
        "• A visual unwrapped card\n\n"
        "For more details, use /help."
    )
    return

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Telegram Unwrapped — Help Guide\n\n"
        "This bot analyzes any public Telegram channel and generates a visual summary card.\n\n"
        "Here’s what I can do:\n"
        "• Fetch all posts from the current year\n"
        "• Identify your top performing post\n"
        "• Generate a custom card summarizing your year\n\n"
        "How to use:\n"
        "1. Send a channel username (example: @mychannel)\n"
        "2. Wait while I fetch and analyze posts\n"
        "3. Receive your generated Unwrapped card\n\n"
    )
    return


async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session_id = str(uuid.uuid4())
    channel_username = update.message.text.strip()
    if not channel_username.startswith("@"):
        await update.message.reply_text("Please send a valid channel username starting with @.")
        return
    
    await update.message.reply_text(f"Fetching messages from {channel_username}... This may take a while.")
    asyncio.create_task(process_summary(update, context, channel_username, session_id))

    return ConversationHandler.END

async def process_summary(update: Update, context: ContextTypes.DEFAULT_TYPE, channel_username, session_id):
    try:
        fetched_count = await fetch_messages_for_year(channel_identifier=channel_username, session_id=session_id)

        if fetched_count:
            json_file_path = f"./{channel_username}-{session_id}.json"
            card_file,top_post_id = await create_summary_card(json_file_path,channel_username=channel_username,session_id=session_id )
            clean_username = channel_username.lstrip("@")
            top_post = f"https://t.me/{clean_username}/{top_post_id}"
        
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=open(card_file, "rb"),
                caption=f"Channel summary for {datetime.now().year} \n your top preforming post of the year is {top_post} "
            )
        else:
            await update.message.reply_text(f"Failed to fetch messages from {channel_username}.")

        return ConversationHandler.END
    
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"An error occurred in session {session_id}: {e}"
        )
    

async def main():
    await telegram_client.client.start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    await app.initialize()
    await app.start()
    print("Bot is running...")
    await app.updater.start_polling()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
