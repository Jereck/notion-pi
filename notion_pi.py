#!/usr/bin/env python3
import time
import requests
from waveshare_epd import epd2in13_V4
from PIL import Image, ImageDraw, ImageFont
import textwrap
from datetime import datetime

# ---------------- CONFIG ----------------
API_URL = "https://1qu1d1h5r5.execute-api.us-east-1.amazonaws.com/notion-dashboard"  # Your hosted API endpoint
REFRESH_INTERVAL = 300  # seconds (5 minutes)
MAX_TASKS_DISPLAY = 5

# Fonts
FONT_HEADER = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
FONT_TASK = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
FONT_FOOTER = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
# ----------------------------------------

def fetch_tasks():
    """Call the hosted API and return a list of task dicts."""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Expecting JSON: {"tasks": [{"name": "...", "status": "...", "priority": "...", "due": "..."}]}
        return data.get("tasks", [])
    except Exception as e:
        print("Error fetching tasks:", e)
        return []

def render_progress_bar(draw, x, y, width, height, completed, total):
    """Draw a horizontal progress bar."""
    if total == 0:
        return
    progress_width = int((completed / total) * width)
    draw.rectangle((x, y, x + width, y + height), outline=0, fill=255)  # background
    draw.rectangle((x, y, x + progress_width, y + height), outline=0, fill=0)  # filled portion

def update_display(tasks, error=False):
    """Render tasks or error info onto the e-ink display."""
    epd = epd2in13_V4.EPD()
    epd.init()
    epd.Clear(0xFF)

    image = Image.new("1", (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(image)

    # Header
    draw.text((5, 0), "Notion Dashboard", font=FONT_HEADER, fill=0)

    y = 25

    if error:
        draw.text((5, y), "⚠ Error fetching tasks", font=FONT_TASK, fill=0)
    elif not tasks:
        draw.text((5, y), "No tasks to display", font=FONT_TASK, fill=0)
    else:
        total = len(tasks)
        completed_count = sum(1 for t in tasks if t.get("status", "").lower() == "done")
        draw.text((5, y), f"Tasks: {total} | Completed: {completed_count}", font=FONT_TASK, fill=0)
        y += 20

        # Progress bar
        render_progress_bar(draw, x=5, y=y, width=epd.height - 10, height=5, completed=completed_count, total=total)
        y += 10

        # Show top tasks
        for task in tasks[:MAX_TASKS_DISPLAY]:
            name = task.get("name", "Unnamed task")
            status = task.get("status", "pending").lower()
            symbol = "✔" if status == "done" else "☐"
            priority = task.get("priority", "").capitalize()
            if priority:
                if priority.lower() == "high":
                    p = "[H]"
                elif priority.lower() == "medium":
                    p = "[M]"
                elif priority.lower() == "low":
                    p = "[L]"
                else:
                    p = f"[{priority[0]}]"
            else:
                p = ""
            due = task.get("due", "")
            line_prefix = f"{symbol} {p}".strip()
            line_text = f"{line_prefix} {name}"
            if due:
                line_text += f" (Due: {due})"
            # Wrap text
            wrapped = textwrap.wrap(line_text, width=25)
            for line in wrapped:
                draw.text((5, y), line, font=FONT_TASK, fill=0)
                y += 15

    # Footer: timestamp
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    draw.text((5, epd.width - 15), f"Updated: {now}", font=FONT_FOOTER, fill=0)

    epd.display(epd.getbuffer(image))
    epd.sleep()

def main():
    while True:
        tasks = fetch_tasks()
        if tasks:
            update_display(tasks)
        else:
            update_display(tasks=[], error=True)
        time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    main()
