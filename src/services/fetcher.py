import asyncio
import json
from datetime import datetime, timezone
from telethon.errors import ChannelPrivateError, ChannelInvalidError
from telethon.tl.functions.channels import GetFullChannelRequest
from src.client import client
from src.utils.helpers import safe_telethon_call

# Global semaphore
PROCESSING_SEMAPHORE = asyncio.Semaphore(1)

async def get_channel_photo(channel_username):
    """Fetches the channel profile picture as bytes."""
    async with PROCESSING_SEMAPHORE:
        try:
            channel = await safe_telethon_call(client.get_entity, channel_username)
            photos = await safe_telethon_call(client.get_profile_photos, channel, limit=1)
            if not photos: return None
            return await safe_telethon_call(client.download_media, photos[0], file=bytes)
        except:
            return None

async def fetch_messages_for_year(channel_identifier, session_id, target_year=None, status_msg=None):
    """
    Fetches messages with Live Progress Updates.
    status_msg: The Telegram message object to edit for progress updates.
    """
    async with PROCESSING_SEMAPHORE:
        current_year = datetime.now().year
        year = target_year if target_year else current_year
        
        start_local = datetime(year, 1, 1, 0, 0, 0)
        end_local = datetime(year + 1, 1, 1, 0, 0, 0)
        start_utc = start_local.astimezone(timezone.utc)
        end_utc = end_local.astimezone(timezone.utc)

        try:
            channel = await safe_telethon_call(client.get_entity, channel_identifier)
            
            if status_msg:
                try: await status_msg.edit_text(f"✅ Found {channel.title}...\nGetting subscriber count...")
                except: pass

            try:
                full_channel_data = await safe_telethon_call(client, GetFullChannelRequest(channel))
                subscribers = full_channel_data.full_chat.participants_count or 0
            except:
                subscribers = 0

            messages_out = []
            count = 0
            
            if status_msg:
                try: await status_msg.edit_text(f"📥 Fetching messages for {year}...\n(This might take a moment)")
                except: pass

            async for msg in client.iter_messages(channel, reverse=False):
                if msg.date < start_utc: break
                if msg.date >= end_utc: continue
                
                media_type = "text"
                if msg.photo: media_type = "photo"
                elif msg.video: media_type = "video"
                elif msg.poll: media_type = "poll"
                elif msg.document: media_type = "document"

                reactions_list = [r.to_dict() for r in msg.reactions.results] if getattr(msg, "reactions", None) else None

                messages_out.append({
                    "id": msg.id,
                    "date": msg.date.isoformat(),
                    "text": msg.message,
                    "media_type": media_type,
                    "views": getattr(msg, "views", 0) or 0,
                    "forwards": getattr(msg, "forwards", 0) or 0,
                    "reactions": reactions_list
                })
                
                count += 1
                
                if status_msg and count % 300 == 0:
                    try:
                        await status_msg.edit_text(f"📥 Fetching messages for {year}...\nFound: {count} messages so far... ⏳")
                    except:
                        pass

            json_filename = f"{channel_identifier}-{session_id}.json"
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump({
                    "channel": str(channel.title),
                    "subscribers": subscribers,
                    "year": year,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "messages_count": len(messages_out),
                    "messages": messages_out
                }, f, ensure_ascii=False, indent=2)

            return len(messages_out), json_filename

        except ChannelPrivateError:
            print("Error: Private")
            return 0, None
        except ChannelInvalidError:
            print("Error: Invalid")
            return 0, None
        except Exception as e:
            print(f"Error: {e}")
            return 0, None