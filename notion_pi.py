#!/usr/bin/env python3
import time
import requests
from waveshare_epd import epd2in13_V4
from PIL import Image, ImageDraw, ImageFont

# ---------------- CONFIG ----------------
API_URL = "https://1qu1d1h5r5.execute-api.us-east-1.amazonaws.com/notion-dashboard"  # Your hosted API endpoint
REFRESH_INTERVAL = 300  # seconds (5 minutes)
FONT = ImageFont.load_default()
# ----------------------------------------

def update_display(tasks):
    """Render task info onto the e-ink display."""
    epd = epd2in13_V4.EPD()
    epd.init()
    epd.Clear(0xFF)

    # Create a blank image
    image = Image.new("1", (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(image)

    # Header
    draw.text((5, 0), "Notion Dashboard", font=FONT, fill=0)

    # Tasks
    y = 20
    for task in tasks[:5]:  # Show top 5 tasks
        draw.text((5, y), f"- {task}", font=FONT, fill=0)
        y += 20

    # Footer: timestamp
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    draw.text((5, epd.width - 15), f"Updated: {now}", font=FONT, fill=0)

    # Send to e-ink
    epd.display(epd.getbuffer(image))
    epd.sleep()

def fetch_tasks():
    """Call the hosted API and return a list of tasks."""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Expecting JSON: {"tasks": ["Task 1", "Task 2", ...]}
        return data.get("tasks", [])
    except Exception as e:
        print("Error fetching tasks:", e)
        return []

def main():
    while True:
        tasks = fetch_tasks()
        if tasks:
            update_display(tasks)
        else:
            print("No tasks to display")
        time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    main()
