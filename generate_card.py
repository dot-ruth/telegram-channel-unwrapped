import json
from datetime import datetime
from collections import Counter
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO
import telegram_client

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

async def create_summary_card(json_file_path, channel_username):
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

    weekday_name = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday"
    ][most_active_weekday]

    CARD_WIDTH, CARD_HEIGHT = 900, 1200
    card = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(card)

    for i in range(CARD_HEIGHT):
        r = 245 + i * (255 - 245) // CARD_HEIGHT
        g = 245 + i * (255 - 245) // CARD_HEIGHT
        b = 255
        draw.line([(0, i), (CARD_WIDTH, i)], fill=(r, g, b))

    title_font = ImageFont.truetype("arialbd.ttf", 50)
    header_font = ImageFont.truetype("arialbd.ttf", 35)
    body_font = ImageFont.truetype("arial.ttf", 28)

    photo_bytes = await get_channel_photo(channel_username)
    if photo_bytes:
        channel_img = Image.open(BytesIO(photo_bytes)).convert("RGB")
    else:
        channel_img = Image.new("RGB", (150, 150), (200, 200, 200))
    channel_img = ImageOps.fit(channel_img, (180, 180), Image.Resampling.LANCZOS)
    mask = Image.new("L", (180, 180), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, 180, 180), fill=255)
    card.paste(channel_img, ((CARD_WIDTH - 180)//2, 40), mask)

    draw.text((CARD_WIDTH//2, 250), data["channel"].split("title='")[1].split("'")[0],
              font=title_font, fill=(30, 30, 50), anchor="ms")

    stats = [
        ("Total Posts", total_posts),
        ("Total Views", total_views),
        ("Average Views", avg_views),
        ("Top Post Views", top_post_views),
        ("Most Active day", weekday_name),
        ("Most Active Month", datetime(1900, most_active_month, 1).strftime('%B')),
    ]

    y = 350
    box_height = 90
    padding = 20

    for label, value in stats:
        rect_color = (230, 240, 255)
        draw.rounded_rectangle(
            [(50, y), (CARD_WIDTH - 50, y + box_height)],
            radius=20, fill=rect_color
        )

        draw.text((70, y + 15), label, font=header_font, fill=(60, 90, 200))

        value_str = str(value)
        max_width = CARD_WIDTH - 200
        lines = []
        while value_str:
            for i in range(len(value_str), 0, -1):
                bbox = draw.textbbox((0, 0), value_str[:i], font=body_font)
                w = bbox[2] - bbox[0]
                if w <= max_width:
                    lines.append(value_str[:i])
                    value_str = value_str[i:]
                    break
        for i, line in enumerate(lines):
            draw.text((400, y + 15 + i * 32), line, font=body_font, fill=(40, 40, 50))

        y += box_height + padding

    card.save(f"{channel_username}.png")
    
    return f"{channel_username}.png",top_post_id
