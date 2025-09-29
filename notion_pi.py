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
# Fonts (make sure these exist on your Pi)
FONT_HEADER = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
FONT_TASK = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
FONT_FOOTER = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
MAX_TASKS_DISPLAY = 5
# ----------------------------------------

def fetch_tasks():
    """Call the hosted API and return a list of tasks."""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("tasks", [])
    except Exception as e:
        print("Error fetching tasks:", e)
        return []

def update_display(tasks, error=False):
    """Render tasks or error info onto the e-ink display."""
    epd = epd2in13_V4.EPD()
    epd.init()
    epd.Clear(0xFF)

    # Create a blank image
    image = Image.new("1", (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(image)

    # Header
    draw.text((5, 0), "Notion Dashboard", font=FONT_HEADER, fill=0)

    y = 25  # Start below header

    if error:
        draw.text((5, y), "⚠ Error fetching tasks", font=FONT_TASK, fill=0)
    elif not tasks:
        draw.text((5, y), "No tasks to display", font=FONT_TASK, fill=0)
    else:
        # Summary line
        total = len(tasks)
        draw.text((5, y), f"Tasks: {total}", font=FONT_TASK, fill=0)
        y += 20

        # Show top N tasks
        for task in tasks[:MAX_TASKS_DISPLAY]:
            # Wrap long text
            wrapped = textwrap.wrap(task, width=25)
            for line in wrapped:
                draw.text((5, y), f"- {line}", font=FONT_TASK, fill=0)
                y += 15

    # Footer: timestamp
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    draw.text((5, epd.width - 15), f"Updated: {now}", font=FONT_FOOTER, fill=0)

    # Send to e-ink
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
