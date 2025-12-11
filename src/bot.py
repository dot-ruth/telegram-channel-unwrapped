import os
import uuid
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)
from src.services.fetcher import fetch_messages_for_year
from src.services.image_gen import create_summary_card

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! Welcome to Telegram Unwrapped Bot.\n\n"
        "Send me any channel username (e.g., @mychannel) and I’ll generate:\n"
        "• Your channel’s yearly summary\n"
        "• The top performing post of the year\n"
        "• A visual unwrapped card\n\n"
        "Creator of this bot: @dot_ruth\n"
        "Contributor: @eyaelBirhanu\n"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Telegram Unwrapped — Help\n"
        "1. Send a channel username (example: @mychannel)\n"
        "2. Wait while I fetch and analyze posts\n"
        "3. Receive your generated Unwrapped card\n"
    )

async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session_id = str(uuid.uuid4())
    if not update.message or not update.message.text: return

    inputs = update.message.text.strip().split()
    channel_username = inputs[0]
    
    if not channel_username.startswith("@"):
        await update.message.reply_text("Please send a valid channel username starting with @.")
        return

    target_year = datetime.now().year
    if len(inputs) > 1:
        if inputs[1].isdigit() and len(inputs[1]) == 4:
            target_year = int(inputs[1])
        else:
            await update.message.reply_text("Invalid year format. Please use: @channel 2023")
            return
    
    current_year = datetime.now().year
    if target_year > current_year:
        await update.message.reply_text("I cannot see into the future! 🔮 Please choose a past year.")
        return
    
    if target_year < 2013:
        await update.message.reply_text("Telegram didn't exist back then! 🦕 Try a year after 2013.")
        return

    status_msg = await update.message.reply_text(f"🔍 Connecting to {channel_username}...")
    
    await process_summary(update, context, channel_username, session_id, target_year, status_msg)

async def process_summary(update: Update, context: ContextTypes.DEFAULT_TYPE, channel_username, session_id, target_year, status_msg):
    try:
        fetched_count, json_file_path = await fetch_messages_for_year(
            channel_identifier=channel_username,
            session_id=session_id,
            target_year=target_year,
            status_msg=status_msg
        )

        if fetched_count and json_file_path:
            
            await status_msg.edit_text("🎨 Calculating stats and painting your card...")

            stats = await create_summary_card(
                json_file_path,
                channel_username=channel_username,
                session_id=session_id
            )

            clean_username = channel_username.lstrip("@")
            top_posts_text = ""
            for i, post in enumerate(stats["top_3_posts"]):
                p_views = post.get('views') or 0
                p_id = post.get('id')
                link = f"https://t.me/{clean_username}/{p_id}"
                top_posts_text += f"{i+1}. <a href='{link}'>Post {p_id}</a> — {p_views:,} views\n"

            mc = stats["media_counts"]
            media_text = f"📷 {mc['photo']} Photos | 🎥 {mc['video']} Videos | 📊 {mc['poll']} Polls"

            caption = (
                f"<b>Channel Summary for {target_year}</b> 🎉\n\n"
                f"<b>📊 Growth & Engagement</b>\n"
                f"• Subscribers: {stats['subscribers']:,}\n"
                f"• Total Posts: {stats['total_posts']:,}\n"
                f"• Total Views: {stats['total_views']:,}\n"
                f"• Total Reactions: {stats['total_reactions']:,}\n"
                f"• Engagement Rate: {stats['engagement_rate']:.2f}%\n\n"
                f"<b>🏆 Top 3 Posts</b>\n{top_posts_text}\n"
                f"<b>🎨 Content Mix</b>\n{media_text}\n\n"
                f"<b>⏰ Activity</b>\n"
                f"• Best Time: {stats['most_active_hour']}\n"
                f"• Best Day: {stats['most_active_day']}\n"
                f"• Best Month: {stats['most_active_month']}\n\n"
                f"<i>@channel_unwrapped_bot #TelegramUnwrapped</i>"
            )

            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=open(stats["file"], "rb"),
                caption=caption,
                parse_mode="HTML"
            )
            
            await status_msg.delete()

            if os.path.exists(stats["file"]): os.remove(stats["file"])
            if os.path.exists(json_file_path): os.remove(json_file_path)
        else:
            await status_msg.edit_text(f"❌ I found 0 messages in {channel_username} for {target_year}.")

    except Exception as e:
        print(f"Bot Error: {e}")
        try:
            await status_msg.edit_text(f"⚠️ An error occurred: {e}")
        except:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error: {e}")
