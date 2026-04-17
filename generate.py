import json
import os
import shutil
import sys
import re

CONFIG_FILE = "config.json"
STATIC_SRC = "static"
OUTPUT_DIR = "output"

def log_error_and_exit(msg):
    print(f"❌ {msg}")
    sys.exit(1)

# ---------- Helper to convert Google Drive link to embed URL ----------
def google_drive_embed(url):
    patterns = [
        r'/file/d/([^/]+)',
        r'id=([^&]+)',
        r'drive\.google\.com.*?[?&]id=([^&]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return f'https://drive.google.com/file/d/{match.group(1)}/preview'
    return url  # fallback (if not a Google Drive link)

# ---------- Load config ----------
if not os.path.exists(CONFIG_FILE):
    log_error_and_exit(f"{CONFIG_FILE} not found!")

try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
except json.JSONDecodeError as e:
    log_error_and_exit(f"Invalid JSON in {CONFIG_FILE}: {e}")

# ---------- Prepare output directory ----------
shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Copy static files if the folder exists
if os.path.exists(STATIC_SRC):
    shutil.copytree(STATIC_SRC, os.path.join(OUTPUT_DIR, "static"))
else:
    print("⚠️  Warning: 'static/' folder not found – no media will be copied.")

# ---------- HTML Templates ----------
INDEX_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3rd Fl WC Shared Space Guide</title>
    <style>
        body {{ font-family: sans-serif; max-width: 600px; margin: 2rem auto; padding: 0 1rem; }}
        .button {{ display: inline-block; padding: 1rem 2rem; margin: 1rem 0; background: #007bff; color: white; text-decoration: none; border-radius: 8px; }}
        img, video, iframe {{ max-width: 100%; height: auto; margin: 1rem 0; }}
        iframe {{ width: 100%; height: 340px; border: none; }}
        .nav {{ margin-top: 2rem; }}
        .nav a {{ margin-right: 1rem; }}
    </style>
</head>
<body>
    <h1>So you want to operate the Westchester 3rd floor Shared Space Screen?</h1>
    {options_html}
</body>
</html>
"""

STEP_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Step {step_num} of {total_steps} – {option_title}</title>
    <style>
        body {{ font-family: sans-serif; max-width: 600px; margin: 2rem auto; padding: 0 1rem; }}
        .button {{ display: inline-block; padding: 1rem 2rem; margin: 1rem 0; background: #007bff; color: white; text-decoration: none; border-radius: 8px; }}
        img, video, iframe {{ max-width: 100%; height: auto; margin: 1rem 0; }}
        iframe {{ width: 100%; height: 340px; border: none; }}
        .nav {{ margin-top: 2rem; }}
        .nav a {{ margin-right: 1rem; }}
    </style>
</head>
<body>
    <h1>{option_title}</h1>
    <p><strong>Step {step_num} of {total_steps}</strong></p>
    <p>{instruction}</p>
    {media}
    <div class="nav">
        {prev_link}
        {next_link}
        <a href="index.html">🏠 Home</a>
    </div>
</body>
</html>
"""

CONGRATS_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Congratulations!</title>
    <style>
        body {{ font-family: sans-serif; max-width: 600px; margin: 2rem auto; padding: 0 1rem; text-align: center; }}
        .button {{ display: inline-block; padding: 1rem 2rem; margin: 1rem 0; background: #28a745; color: white; text-decoration: none; border-radius: 8px; }}
    </style>
</head>
<body>
    <h1>🎉 Good job! 🎉</h1>
    <p>You have successfully {message}.</p>
    <a href="index.html" class="button">Start another task</a>
</body>
</html>
"""

# ---------- Generate index page ----------
options_html = ""
for opt in config.get("options", []):
    first_step = f"{opt['id']}_step1.html"
    options_html += f'<a href="{first_step}" class="button">{opt["title"]}</a><br>'

with open(os.path.join(OUTPUT_DIR, "index.html"), "w") as f:
    f.write(INDEX_TEMPLATE.format(options_html=options_html))

# ---------- Generate step pages for each option ----------
for opt in config.get("options", []):
    steps = opt.get("steps", [])
    total = len(steps)
    if total == 0:
        print(f"⚠️  Warning: No steps for option '{opt.get('id')}'")

    for i, step in enumerate(steps, start=1):
        # Determine media HTML
        if "video_url" in step:
            embed_url = google_drive_embed(step["video_url"])
            media = f'<iframe src="{embed_url}" allow="autoplay; encrypted-media" allowfullscreen title="{step.get("alt", "Video")}"></iframe>'
        elif "video" in step:
            media = f'<video controls alt="{step.get("alt", "")}"><source src="static/videos/{step["video"]}" type="video/mp4">Your browser does not support the video tag.</video>'
        elif "image" in step:
            media = f'<img src="static/images/{step["image"]}" alt="{step.get("alt", "")}">'
        else:
            media = ""  # no media

        # Navigation links
        prev_link = f'<a href="{opt["id"]}_step{i-1}.html" class="button">⬅ Previous</a>' if i > 1 else ""
        if i < total:
            next_link = f'<a href="{opt["id"]}_step{i+1}.html" class="button">Next ➔</a>'
        else:
            next_link = f'<a href="{opt["id"]}_congrats.html" class="button">Finish ➔</a>'

        filename = f"{opt['id']}_step{i}.html"
        page = STEP_TEMPLATE.format(
            option_title=opt["title"],
            step_num=i,
            total_steps=total,
            instruction=step.get("instruction", ""),
            media=media,
            prev_link=prev_link,
            next_link=next_link
        )
        with open(os.path.join(OUTPUT_DIR, filename), "w") as f:
            f.write(page)

    # Congratulations page for this option
    congrats_file = f"{opt['id']}_congrats.html"
    with open(os.path.join(OUTPUT_DIR, congrats_file), "w") as f:
        f.write(CONGRATS_TEMPLATE.format(message=opt["title"].lower()))

print("✅ Site generated successfully!")
