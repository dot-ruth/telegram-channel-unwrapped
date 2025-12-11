import json
import os
from datetime import datetime
from collections import Counter
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance
from io import BytesIO
from src.config import FONT_PATH
from src.utils.helpers import format_hour
from src.services.fetcher import get_channel_photo

def draw_glass_rect(draw, xy, radius=30):
    """
    Draws a 'Smoked Glass' box with high transparency.
    """
    draw.rounded_rectangle(xy, radius=radius, fill=(20, 20, 20, 160)) 
    draw.rounded_rectangle(xy, radius=radius, outline=(255, 255, 255, 40), width=2)

async def create_summary_card(json_file_path, channel_username, session_id):
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = data["messages"]
    subscribers = data.get("subscribers") or 0
    year = data.get("year", datetime.now().year)

    # ---------------- ANALYTICS ----------------
    total_posts = len(messages)
    total_views = sum((msg.get("views") or 0) for msg in messages)
    avg_views = total_views // total_posts if total_posts else 0

    total_reactions = 0
    media_counts = {"photo": 0, "video": 0, "text": 0, "poll": 0}
    
    for msg in messages:
        if msg.get("reactions"):
            for r in msg["reactions"]:
                total_reactions += r.get("count", 0)
        
        m_type = msg.get("media_type", "text")
        if m_type in media_counts:
            media_counts[m_type] += 1
        else:
            media_counts["text"] += 1

    engagement_rate = (total_reactions / total_views * 100) if total_views > 0 else 0.0

    sorted_by_views = sorted(messages, key=lambda x: (x.get("views") or 0), reverse=True)
    top_3_posts = sorted_by_views[:3]
    top_post = top_3_posts[0] if top_3_posts else {}
    top_post_id = top_post.get("id", "")
    top_post_views = top_post.get("views") or 0

    if messages:
        months = [datetime.fromisoformat(msg["date"]).month for msg in messages]
        most_active_month = Counter(months).most_common(1)[0][0]
        days = [datetime.fromisoformat(msg["date"]).weekday() for msg in messages]
        most_active_weekday = Counter(days).most_common(1)[0][0]
        hours = [datetime.fromisoformat(msg["date"]).hour for msg in messages]
        most_active_hour = Counter(hours).most_common(1)[0][0]
    else:
        most_active_month = 1; most_active_weekday = 0; most_active_hour = 12

    weekday_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][most_active_weekday]
    month_name = datetime(1900, most_active_month, 1).strftime('%B')

    # ---------------- DESIGN SETUP ----------------
    CARD_WIDTH, CARD_HEIGHT = 1000, 1550
    
    try:
        title_font = ImageFont.truetype(FONT_PATH, size=55)
        header_font = ImageFont.truetype(FONT_PATH, size=32)
        value_font = ImageFont.truetype(FONT_PATH, size=52)
        small_font = ImageFont.truetype(FONT_PATH, size=24)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        value_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    card = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (15, 15, 15))
    
    # 1. Background
    photo_bytes = await get_channel_photo(channel_username)
    if photo_bytes:
        bg_img = Image.open(BytesIO(photo_bytes)).convert("RGB")
        bg_img = ImageOps.fit(bg_img, (CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS)
        
        bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=15)) 
        
        enhancer = ImageEnhance.Brightness(bg_img)
        bg_img = enhancer.enhance(0.65) 
        card.paste(bg_img, (0, 0))
    
    draw = ImageDraw.Draw(card, "RGBA")

    # 2. PFP & Header
    PFP_SIZE = 220
    pfp_y = 100
    pfp_x = (CARD_WIDTH - PFP_SIZE) // 2
    
    if photo_bytes:
        pfp_img = Image.open(BytesIO(photo_bytes)).convert("RGB")
        pfp_img = ImageOps.fit(pfp_img, (PFP_SIZE, PFP_SIZE), Image.Resampling.LANCZOS)
        mask = Image.new("L", (PFP_SIZE, PFP_SIZE), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, PFP_SIZE, PFP_SIZE), fill=255)
        card.paste(pfp_img, (pfp_x, pfp_y), mask)
        draw.ellipse((pfp_x-4, pfp_y-4, pfp_x+PFP_SIZE+4, pfp_y+PFP_SIZE+4), outline=(255,255,255, 150), width=2)

    try:
        raw = data["channel"]
        if "title='" in raw:
            channel_name = raw.split("title='")[1].split("',")[0]
        elif 'title="' in raw:
            channel_name = raw.split('title="')[1].split('",')[0]
        else:
            channel_name = channel_username
    except:
        channel_name = channel_username

    channel_name = channel_name.strip()
    text_start_y = pfp_y + PFP_SIZE + 60 

    draw.text(
        (CARD_WIDTH//2, text_start_y),
        channel_name,
        font=title_font,
        fill="white",
        anchor="ms"
    )
    draw.text(
        (CARD_WIDTH//2, text_start_y + 60),
        f"{year} UNWRAPPED",
        font=small_font,
        fill=(200, 200, 200),
        anchor="ms"
    )

    # 2. Glass Grid Settings
    GRID_START_Y = text_start_y + 120
    BOX_WIDTH = 400
    BOX_HEIGHT = 160
    GAP = 60

    LEFT_X = (CARD_WIDTH - (2 * BOX_WIDTH) - GAP) // 2
    RIGHT_X = LEFT_X + BOX_WIDTH + GAP

    def draw_stat_box(label, value, x, y):
        draw_glass_rect(draw, [x, y, x + BOX_WIDTH, y + BOX_HEIGHT])

        cx = x + (BOX_WIDTH // 2)

        draw.text(
            (cx, y + 45),
            label,
            font=header_font,
            fill=(220, 220, 220),
            anchor="ms"
        )
        draw.text(
            (cx, y + 105),
            str(value),
            font=value_font,
            fill="white",
            anchor="ms"
        )

    # --- ROW 1 ---
    draw_stat_box("Current Subs", f"{subscribers:,}", LEFT_X, GRID_START_Y)
    draw_stat_box("Total Views", f"{total_views:,}", RIGHT_X, GRID_START_Y)

    # --- ROW 2 ---
    ROW2_Y = GRID_START_Y + BOX_HEIGHT + GAP
    draw_stat_box("Total Posts", f"{total_posts:,}", LEFT_X, ROW2_Y)
    draw_stat_box("Engagement", f"{engagement_rate:.2f}%", RIGHT_X, ROW2_Y)

    # 3. Activity Row (wide 3-column box)
    ROW3_Y = ROW2_Y + BOX_HEIGHT + GAP
    WIDE_WIDTH = (BOX_WIDTH * 2) + GAP
    draw_glass_rect(draw, [LEFT_X, ROW3_Y, LEFT_X + WIDE_WIDTH, ROW3_Y + 180])

    col_w = WIDE_WIDTH // 3

    def draw_stat_col(idx, val, label):
        cx = LEFT_X + (col_w * idx) + (col_w // 2)

        draw.text(
            (cx, ROW3_Y + 75),
            str(val),
            font=value_font,
            fill="white",
            anchor="ms"
        )
        draw.text(
            (cx, ROW3_Y + 135),
            label,
            font=small_font,
            fill=(180, 180, 180),
            anchor="ms"
        )

    draw_stat_col(0, format_hour(most_active_hour), "Best Time")
    draw_stat_col(1, weekday_name[:3], "Best Day")
    draw_stat_col(2, month_name[:3], "Best Month")

    # 4. Media Breakdown Header
    ROW4_Y = ROW3_Y + 240
    draw.text(
        (CARD_WIDTH // 2, ROW4_Y),
        "Content Distribution",
        font=header_font,
        fill="white",
        anchor="ms"
    )
    
    total_media = sum(media_counts.values()) or 1
    w_photo = int((media_counts["photo"] / total_media) * WIDE_WIDTH)
    w_video = int((media_counts["video"] / total_media) * WIDE_WIDTH)
    w_poll = int((media_counts["poll"] / total_media) * WIDE_WIDTH)
    w_text = WIDE_WIDTH - w_photo - w_video - w_poll 
    
    bar_y = ROW4_Y + 30
    bar_h = 25
    curr_x = LEFT_X
    
    segments = [
        (w_photo, "#3498db", "Photos"),  
        (w_video, "#9b59b6", "Videos"),  
        (w_poll,  "#f1c40f", "Polls"),   
        (w_text,  "#2ecc71", "Text")     
    ]
    
    for width, color, label in segments:
        if width > 0:
            draw.rectangle([curr_x, bar_y, curr_x+width, bar_y+bar_h], fill=color)
            if width > 40:
                draw.text((curr_x + width//2, bar_y + 50), label, font=small_font, fill=color, anchor="mt")
            curr_x += width

    # Footer
    draw.text((CARD_WIDTH//2, CARD_HEIGHT - 60), "@channel_unwrapped_bot", font=small_font, fill=(200,200,200), anchor="ms")

    output_buffer = BytesIO()
    card.save(output_buffer, format="PNG")
    output_buffer.seek(0)
    output_filename = f"{channel_username}-{session_id}.png"
    card.save(output_filename)
    
    return {
        "file": output_filename,
        "total_posts": total_posts,
        "total_views": total_views,
        "avg_views": avg_views,
        "subscribers": subscribers,
        "total_reactions": total_reactions,
        "engagement_rate": engagement_rate,
        "media_counts": media_counts,
        "top_3_posts": top_3_posts,
        "most_reacted_id": None,
        "most_active_hour": format_hour(most_active_hour),
        "most_active_day": weekday_name,
        "most_active_month": month_name
    }