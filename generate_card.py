import json
from datetime import datetime
from collections import Counter
import re
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from io import BytesIO
import telegram_client

def format_hour(h):
    suffix = "AM" if h < 12 else "PM"
    hour = h % 12
    hour = 12 if hour == 0 else hour
    return f"{hour} {suffix}"

async def get_channel_photo(channel_username):
    try:
        channel = await telegram_client.client.get_entity(channel_username)
        photos = await telegram_client.client.get_profile_photos(channel, limit=1)
        if not photos:
            return None
        photo_bytes = await telegram_client.client.download_media(photos[0], file=bytes)
        return photo_bytes
    except Exception as e:
        print(f"Error fetching channel photo: {e}")
        return None

async def create_summary_card(json_file_path, channel_username, session_id):
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = data["messages"]

    total_posts = len(messages)
    total_views = sum((msg.get("views") or 0) for msg in messages)
    top_post = max(messages, key=lambda x: (x.get("views") or 0))
    top_post_id = top_post.get("id", "")
    top_post_views = top_post.get("views") or 0
    months = [datetime.fromisoformat(msg["date"]).month for msg in messages]
    most_active_month = Counter(months).most_common(1)[0][0]
    avg_views = total_views // total_posts if total_posts else 0
    days = [datetime.fromisoformat(msg["date"]).weekday() for msg in messages]
    most_active_weekday = Counter(days).most_common(1)[0][0]
    hours = [datetime.fromisoformat(msg["date"]).hour for msg in messages]
    most_active_hour = Counter(hours).most_common(1)[0][0]

    weekday_name = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday"
    ][most_active_weekday]

    CARD_WIDTH, CARD_HEIGHT = 900, 1300
    BACKGROUND_COLOR = (40, 40, 40)

    title_font = ImageFont.load_default(size=55)
    header_font = ImageFont.load_default(size=30)
    value_font = ImageFont.load_default(size=30)
    small_font = ImageFont.load_default(size=24)
    
    card = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(card)

    photo_bytes = await get_channel_photo(channel_username)
    if photo_bytes:
        channel_img = Image.open(BytesIO(photo_bytes)).convert("RGB")
        background_img = ImageOps.fit(channel_img, (CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS)
        background_img = background_img.filter(ImageFilter.GaussianBlur(radius=5))
        card.paste(background_img, (0, 0))
        cover = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), (50, 50, 50, 180)) 
        
        card = Image.alpha_composite(card.convert('RGBA'), cover)
        draw = ImageDraw.Draw(card) 
        
    PFP_SIZE = 180
    if photo_bytes:
        pfp_img = Image.open(BytesIO(photo_bytes)).convert("RGB")
    else:
        pfp_img = Image.new("RGB", (PFP_SIZE, PFP_SIZE), (100, 100, 100)) # Placeholder
        
    pfp_img = ImageOps.fit(pfp_img, (PFP_SIZE, PFP_SIZE), Image.Resampling.LANCZOS)
    mask = Image.new("L", (PFP_SIZE, PFP_SIZE), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, PFP_SIZE, PFP_SIZE), fill=255)
    pfp_x = (CARD_WIDTH - PFP_SIZE) // 2
    pfp_y = 50 
    card.paste(pfp_img, (pfp_x, pfp_y), mask)
    draw.ellipse((pfp_x - 5, pfp_y - 5, pfp_x + PFP_SIZE + 5, pfp_y + PFP_SIZE + 5), 
                 outline=(255, 255, 255, 100), width=3)


    channel_str = data["channel"]

    # Look for title="...anything..." safely
    match = re.search(r'title="(.*?)"', channel_str)
    if match:
        channel_name = match.group(1)
    else:
        channel_name = "Unknown Channel"
    draw.text((CARD_WIDTH//2, pfp_y + PFP_SIZE + 70), channel_name,
              font=title_font, fill=(255, 255, 255), anchor="ms")
              
    draw.text((CARD_WIDTH//2, pfp_y + PFP_SIZE + 130), f"{data['year']} UNWRAPPED",
              font=small_font, fill=(200, 200, 200), anchor="ms")


    stats = [
        ("Total Posts", total_posts, 0),
        ("Total Views", total_views, 1),
        ("Average Views", avg_views, 2),
        ("Top Post Views", top_post_views, 3),
        ("Most Active hour", format_hour(most_active_hour), 4),
        ("Most Active day", weekday_name, 5),
        ("Most Active Month", datetime(1900, most_active_month, 1).strftime('%B'), 6),
        
    ]

    START_Y = 400
    SPACING_Y = 120
    BOX_H = 80
    TEXT_H_OFFSET = 25

    for label, value, index in stats:
        y = START_Y + (SPACING_Y * index)
        rect_color = (50, 50, 50, 180) 
    
        draw.rounded_rectangle(
            [(50, y), (CARD_WIDTH - 50, y + BOX_H)],
            radius=20, 
            fill=rect_color,       
            outline=(255, 255, 255, 100),   
            width=3  
        )
        
        draw.text((75, y + TEXT_H_OFFSET), label, font=header_font, fill=(255, 255, 255))
        value_str = str(value)
        value_x = CARD_WIDTH - 75
        
        draw.text((value_x, y + TEXT_H_OFFSET), value_str, 
                  font=value_font, fill=(255, 255, 255), 
                  anchor="ra")

    output_buffer = BytesIO()
    card.save(output_buffer, format="PNG")
    output_buffer.seek(0)
    
    output_filename = f"{channel_username}-{session_id}.png"
    card.save(output_filename)
    
    return output_filename, top_post_id