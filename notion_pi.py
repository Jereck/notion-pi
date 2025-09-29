#!/usr/bin/env python3
import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from waveshare_epd import epd2in13_V4
from PIL import Image, ImageDraw, ImageFont
import textwrap
from notion_client import Client

load_dotenv()

# ---------------- CONFIG ----------------
REFRESH_INTERVAL_DISPLAY = 300  # refresh e-ink every 5 minutes
REFRESH_INTERVAL_NOTION = 1800  # fetch new tasks every 30 minutes
MAX_TASKS_DISPLAY = 5
CACHE_FILE = "tasks_cache.json"

# Fonts
FONT_HEADER = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
FONT_TASK = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
FONT_FOOTER = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

# Notion setup
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
notion = Client(auth=NOTION_TOKEN)

# ---------------- HELPERS ----------------
def fetch_today_tasks():
    """Fetch tasks from Notion due today."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    try:
        response = notion.databases.query(
            database_id=DATABASE_ID,
            filter={
                "property": "Due",
                "date": {"equals": today_str}
            }
        )
        tasks = []
        for result in response.get("results", []):
            props = result["properties"]
            task = {
                "name": props["Name"]["title"][0]["text"]["content"] if props["Name"]["title"] else "Unnamed",
                "status": props.get("Status", {}).get("select", {}).get("name", "pending"),
                "priority": props.get("Priority", {}).get("select", {}).get("name", "")
            }
            tasks.append(task)
        save_cache(tasks)
        return tasks
    except Exception as e:
        print("Error fetching tasks from Notion:", e)
        return load_cache()  # fallback to cached tasks

def save_cache(tasks):
    with open(CACHE_FILE, "w") as f:
        json.dump(tasks, f)

def load_cache():
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def render_progress_bar(draw, x, y, width, height, completed, total):
    if total == 0:
        return
    progress_width = int((completed / total) * width)
    draw.rectangle((x, y, x + width, y + height), outline=0, fill=255)
    draw.rectangle((x, y, x + progress_width, y + height), outline=0, fill=0)

def update_display(tasks):
    """Render tasks onto e-ink display."""
    epd = epd2in13_V4.EPD()
    epd.init()
    epd.Clear(0xFF)

    image = Image.new("1", (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(image)

    # Header
    draw.text((5, 0), "Today's Tasks", font=FONT_HEADER, fill=0)

    y = 25
    if not tasks:
        draw.text((5, y), "No tasks for today!", font=FONT_TASK, fill=0)
    else:
        total = len(tasks)
        completed_count = sum(1 for t in tasks if t.get("status", "").lower() == "done")
        draw.text((5, y), f"Tasks: {total} | Completed: {completed_count}", font=FONT_TASK, fill=0)
        y += 20

        # Progress bar
        render_progress_bar(draw, x=5, y=y, width=epd.height - 10, height=5,
                            completed=completed_count, total=total)
        y += 10

        # Show top tasks
        for task in tasks[:MAX_TASKS_DISPLAY]:
            name = task.get("name", "Unnamed")
            status = task.get("status", "pending").lower()
            symbol = "✔" if status == "done" else "☐"
            priority = task.get("priority", "").capitalize()
            if priority:
                p = {"High": "[H]", "Medium": "[M]", "Low": "[L]"}.get(priority, f"[{priority[0]}]")
            else:
                p = ""
            line_text = f"{symbol} {p} {name}".strip()
            wrapped = textwrap.wrap(line_text, width=25)
            for line in wrapped:
                draw.text((5, y), line, font=FONT_TASK, fill=0)
                y += 15

    # Footer
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    draw.text((5, epd.width - 15), f"Updated: {now}", font=FONT_FOOTER, fill=0)

    epd.display(epd.getbuffer(image))
    epd.sleep()

# ---------------- MAIN LOOP ----------------
def main():
    last_fetch = 0
    tasks = []

    while True:
        now = time.time()
        # Fetch new tasks every REFRESH_INTERVAL_NOTION
        if now - last_fetch > REFRESH_INTERVAL_NOTION:
            tasks = fetch_today_tasks()
            last_fetch = now

        update_display(tasks)
        time.sleep(REFRESH_INTERVAL_DISPLAY)

if __name__ == "__main__":
    main()
