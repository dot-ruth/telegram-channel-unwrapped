import asyncio
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
CHANNEL_USERNAME = range(1)

async def fetch_messages_for_year(channel_identifier, max_messages=None):
    year = datetime.now().year

    start_local = datetime(year, 1, 1, 0, 0, 0)
    start_utc = start_local.astimezone(timezone.utc)

    try:
        channel = await telegram_client.client.get_entity(channel_identifier)
        messages_out = []
        count = 0

        async for msg in telegram_client.client.iter_messages(channel, reverse=False):
            if msg.date < start_utc:
                continue
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
            if max_messages and count >= max_messages:
                break

        with open(f"{channel_identifier}.json", "w", encoding="utf-8") as f:
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
        "Hi! Let's get your Unwrapped.\n"
        "Please send me the channel username (e.g., @mychannel):"
    )
    return CHANNEL_USERNAME

async def receive_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_username = update.message.text.strip()
    await update.message.reply_text(f"Fetching messages from {channel_username}... This may take a while.")

    fetched_count = await fetch_messages_for_year(channel_identifier=channel_username)

    if fetched_count:
        json_file_path = f"./{channel_username}.json"
        card_file,top_post_id = await create_summary_card(json_file_path,channel_username=channel_username)
        clean_username = channel_username.lstrip("@")
        top_post = f"https://t.me/{clean_username}/{top_post_id}"
        
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(card_file, "rb"),
            caption=f"Channel summary for {datetime.now().year} \n your top preforming post is {top_post} "
        )
    else:
        await update.message.reply_text(f"Failed to fetch messages from {channel_username}.")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

async def main():
    await telegram_client.client.start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHANNEL_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_channel)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv_handler)
    await app.initialize()
    await app.start()
    print("Bot is running...")
    await app.updater.start_polling()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
