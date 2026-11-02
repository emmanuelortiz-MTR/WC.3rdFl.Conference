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
    return url

# ---------- Helper to get localized text ----------
def get_localized_text(data, lang='en'):
    """Extract text from a field that might be a string or a language object"""
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        return data.get(lang, data.get('en', str(data)))
    return str(data)

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

# Copy static files securely
if os.path.exists(STATIC_SRC):
    dest_static = os.path.join(OUTPUT_DIR, "static")
    os.makedirs(dest_static, exist_ok=True)
    
    # Manually walk through the folders and copy files
    for root, dirs, files in os.walk(STATIC_SRC):
        # Figure out the destination path
        rel_path = os.path.relpath(root, STATIC_SRC)
        dest_dir = os.path.join(dest_static, rel_path) if rel_path != "." else dest_static
        
        os.makedirs(dest_dir, exist_ok=True)
        
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_dir, file)
            shutil.copy2(src_file, dest_file)
            
    print("✅ Static files and images copied successfully.")
else:
    print("⚠️  Warning: 'static/' folder not found – no media will be copied.")

# ---------- HTML Templates ----------
# Notice the cookie clearing script is ONLY in the INDEX_TEMPLATE
INDEX_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <script>
        document.cookie.split(";").forEach(function(c) {{ 
            document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
        }});
        localStorage.removeItem('preferredLanguage');
    </script>
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
        .lang-toggle {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            z-index: 1000;
        }}
        .lang-toggle:hover {{
            background: #218838;
        }}
        .lang-en, .lang-es {{
            display: none;
        }}
        .lang-en.active, .lang-es.active {{
            display: block;
        }}
    </style>
</head>
<body>
    <button class="lang-toggle" onclick="toggleLanguage()">Español</button>
    <h1>
        <span class="lang-en active">So you want to operate the Westchester 3rd floor Shared Space Screen?</span>
        <span class="lang-es">¿Quieres operar la pantalla del espacio compartido del 3er piso de Westchester?</span>
    </h1>
    <div id="content">
        {options_html}
    </div>
    <script>
        let currentLang = 'en';
        
        function toggleLanguage() {{
            const toggleBtn = document.querySelector('.lang-toggle');
            if (currentLang === 'en') {{
                currentLang = 'es';
                toggleBtn.textContent = 'English';
            }} else {{
                currentLang = 'en';
                toggleBtn.textContent = 'Español';
            }}
            updateLanguage(currentLang);
        }}
        
        function updateLanguage(lang) {{
            document.querySelectorAll('.lang-en, .lang-es').forEach(el => {{
                el.classList.remove('active');
                if (el.classList.contains(`lang-${{lang}}`)) {{
                    el.classList.add('active');
                }}
            }});
            localStorage.setItem('preferredLanguage', lang);
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            const savedLang = localStorage.getItem('preferredLanguage') || 'en';
            currentLang = savedLang;
            if (savedLang === 'es') {{
                document.querySelector('.lang-toggle').textContent = 'English';
            }}
            updateLanguage(savedLang);
        }});
    </script>
</body>
</html>
"""

# Notice the cookie clearing script is REMOVED from here
STEP_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Step {step_num} of {total_steps} – {option_title_en}</title>
    <style>
        body {{ font-family: sans-serif; max-width: 600px; margin: 2rem auto; padding: 0 1rem; }}
        .button {{ display: inline-block; padding: 1rem 2rem; margin: 1rem 0; background: #007bff; color: white; text-decoration: none; border-radius: 8px; }}
        img, video, iframe {{ max-width: 100%; height: auto; margin: 1rem 0; }}
        iframe {{ width: 100%; height: 340px; border: none; }}
        .nav {{ margin-top: 2rem; }}
        .nav a {{ margin-right: 1rem; }}
        .lang-toggle {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            z-index: 1000;
        }}
        .lang-toggle:hover {{
            background: #218838;
        }}
        .lang-en, .lang-es, .instruction-en, .instruction-es {{
            display: none;
        }}
        .lang-en.active, .lang-es.active, .instruction-en.active, .instruction-es.active {{
            display: block;
        }}
        .step-counter-en, .step-counter-es {{
            display: none;
        }}
        .step-counter-en.active, .step-counter-es.active {{
            display: inline;
        }}
    </style>
</head>
<body>
    <button class="lang-toggle" onclick="toggleLanguage()">Español</button>
    <h1>
        <span class="lang-en active">{option_title_en}</span>
        <span class="lang-es">{option_title_es}</span>
    </h1>
    <p><strong>
        <span class="lang-en active step-counter-en">Step {step_num} of {total_steps}</span>
        <span class="lang-es step-counter-es">Paso {step_num} de {total_steps}</span>
    </strong></p>
    <div class="instruction-en active">{instruction_en}</div>
    <div class="instruction-es">{instruction_es}</div>
    {media}
    <div class="nav">
        {prev_link}
        {next_link}
        <a href="index.html" class="button">
            <span class="lang-en active">🏠 Home</span>
            <span class="lang-es">🏠 Inicio</span>
        </a>
    </div>
    <script>
        let currentLang = 'en';
        
        function toggleLanguage() {{
            const toggleBtn = document.querySelector('.lang-toggle');
            if (currentLang === 'en') {{
                currentLang = 'es';
                toggleBtn.textContent = 'English';
            }} else {{
                currentLang = 'en';
                toggleBtn.textContent = 'Español';
            }}
            updateLanguage(currentLang);
        }}
        
        function updateLanguage(lang) {{
            document.querySelectorAll('.lang-en, .lang-es, .instruction-en, .instruction-es, .step-counter-en, .step-counter-es').forEach(el => {{
                el.classList.remove('active');
                if (el.classList.contains(`lang-${{lang}}`) || 
                    el.classList.contains(`instruction-${{lang}}`) ||
                    el.classList.contains(`step-counter-${{lang}}`)) {{
                    el.classList.add('active');
                }}
            }});
            localStorage.setItem('preferredLanguage', lang);
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            const savedLang = localStorage.getItem('preferredLanguage') || 'en';
            currentLang = savedLang;
            if (savedLang === 'es') {{
                document.querySelector('.lang-toggle').textContent = 'English';
            }}
            updateLanguage(savedLang);
        }});
    </script>
</body>
</html>
"""

# Notice the cookie clearing script is REMOVED from here
CONGRATS_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Congratulations!</title>
    <style>
        body {{ font-family: sans-serif; max-width: 600px; margin: 2rem auto; padding: 0 1rem; text-align: center; }}
        .button {{ display: inline-block; padding: 1rem 2rem; margin: 1rem 0; background: #28a745; color: white; text-decoration: none; border-radius: 8px; }}
        .lang-toggle {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            z-index: 1000;
        }}
        .lang-toggle:hover {{
            background: #218838;
        }}
        .lang-en, .lang-es {{
            display: none;
        }}
        .lang-en.active, .lang-es.active {{
            display: block;
        }}
    </style>
</head>
<body>
    <button class="lang-toggle" onclick="toggleLanguage()">Español</button>
    <h1>
        <span class="lang-en active">🎉 Good job! 🎉</span>
        <span class="lang-es">🎉 ¡Buen trabajo! 🎉</span>
    </h1>
    <p>
        <span class="lang-en active">You have successfully {message_en}.</span>
        <span class="lang-es">Has completado exitosamente {message_es}.</span>
    </p>
    <a href="index.html" class="button">
        <span class="lang-en active">Start another task</span>
        <span class="lang-es">Iniciar otra tarea</span>
    </a>
    <script>
        let currentLang = 'en';
        
        function toggleLanguage() {{
            const toggleBtn = document.querySelector('.lang-toggle');
            if (currentLang === 'en') {{
                currentLang = 'es';
                toggleBtn.textContent = 'English';
            }} else {{
                currentLang = 'en';
                toggleBtn.textContent = 'Español';
            }}
            updateLanguage(currentLang);
        }}
        
        function updateLanguage(lang) {{
            document.querySelectorAll('.lang-en, .lang-es').forEach(el => {{
                el.classList.remove('active');
                if (el.classList.contains(`lang-${{lang}}`)) {{
                    el.classList.add('active');
                }}
            }});
            localStorage.setItem('preferredLanguage', lang);
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            const savedLang = localStorage.getItem('preferredLanguage') || 'en';
            currentLang = savedLang;
            if (savedLang === 'es') {{
                document.querySelector('.lang-toggle').textContent = 'English';
            }}
            updateLanguage(savedLang);
        }});
    </script>
</body>
</html>
"""

# ---------- Helper function to generate media HTML ----------
def generate_media_html(step, lang='en'):
    """Generate HTML for media (video, single image, or multiple images)"""
    if "video_url" in step:
        embed_url = google_drive_embed(step["video_url"])
        alt_text = get_localized_text(step.get("alt"), lang)
        return f'<iframe src="{embed_url}" allow="autoplay; encrypted-media" allowfullscreen title="{alt_text}"></iframe>'
    
    if "video" in step:
        alt_text = get_localized_text(step.get("alt"), lang)
        return f'<video controls alt="{alt_text}"><source src="static/videos/{step["video"]}" type="video/mp4">Your browser does not support the video tag.</video>'
    
    if "images" in step:
        images_html = '<div class="image-grid">'
        for img in step["images"]:
            alt_text = get_localized_text(img.get("alt"), lang)
            images_html += f'<img src="static/images/{img["src"]}" alt="{alt_text}">'
        images_html += '</div>'
        return images_html
    
    if "image" in step:
        alt_text = get_localized_text(step.get("alt"), lang)
        return f'<img src="static/images/{step["image"]}" alt="{alt_text}">'
    
    return ""

# ---------- Generate index page ----------
options_html = ""
for opt in config.get("options", []):
    first_step = f"{opt['id']}_step1.html"
    title_en = get_localized_text(opt["title"], 'en')
    title_es = get_localized_text(opt["title"], 'es')
    options_html += f'<a href="{first_step}" class="button lang-en active">{title_en}</a><br>'
    options_html += f'<a href="{first_step}" class="button lang-es">{title_es}</a><br>'

with open(os.path.join(OUTPUT_DIR, "index.html"), "w") as f:
    f.write(INDEX_TEMPLATE.format(options_html=options_html))

# ---------- Generate step pages for each option ----------
for opt in config.get("options", []):
    steps = opt.get("steps", [])
    total = len(steps)
    if total == 0:
        print(f"⚠️  Warning: No steps for option '{opt.get('id')}'")

    option_title_en = get_localized_text(opt["title"], 'en')
    option_title_es = get_localized_text(opt["title"], 'es')

    for i, step in enumerate(steps, start=1):
        instruction_en = get_localized_text(step.get("instruction"), 'en')
        instruction_es = get_localized_text(step.get("instruction"), 'es')
        
        # Generate media HTML (use 'en' for the alt text since we show both languages in the image)
        media = generate_media_html(step, 'en')

        # Navigation links (now bilingual)
        prev_link = f'<a href="{opt["id"]}_step{i-1}.html" class="button"><span class="lang-en active">⬅ Previous</span><span class="lang-es">⬅ Anterior</span></a>' if i > 1 else ""
        if i < total:
            next_link = f'<a href="{opt["id"]}_step{i+1}.html" class="button"><span class="lang-en active">Next ➔</span><span class="lang-es">Siguiente ➔</span></a>'
        else:
            next_link = f'<a href="{opt["id"]}_congrats.html" class="button"><span class="lang-en active">Finish ➔</span><span class="lang-es">Finalizar ➔</span></a>'

        filename = f"{opt['id']}_step{i}.html"
        page = STEP_TEMPLATE.format(
            option_title_en=option_title_en,
            option_title_es=option_title_es,
            step_num=i,
            total_steps=total,
            instruction_en=instruction_en,
            instruction_es=instruction_es,
            media=media,
            prev_link=prev_link,
            next_link=next_link
        )
        with open(os.path.join(OUTPUT_DIR, filename), "w") as f:
            f.write(page)

    # Congratulations page for this option
    congrats_file = f"{opt['id']}_congrats.html"
    message_en = option_title_en.lower()
    message_es = option_title_es.lower()
    with open(os.path.join(OUTPUT_DIR, congrats_file), "w") as f:
        f.write(CONGRATS_TEMPLATE.format(message_en=message_en, message_es=message_es))

print("✅ Site generated successfully with bilingual support!")
