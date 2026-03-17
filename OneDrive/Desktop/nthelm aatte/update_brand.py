import os
import shutil

ROOT_DIR = r"c:\Users\achua\OneDrive\Desktop\nthelm aatte"
LOGO_SRC = r"C:\Users\achua\.gemini\antigravity\brain\45bae074-8619-49c7-b704-000c92030ab1\janavaakya_logo_1772551414568.png"
LOGO_DEST = os.path.join(ROOT_DIR, "static", "img", "janavaakya_logo.png")

# Copy the logo
try:
    shutil.copy2(LOGO_SRC, LOGO_DEST)
    print(f"Copied logo to {LOGO_DEST}")
except FileNotFoundError:
    print(f"Failed to find logo at {LOGO_SRC}")

search_text = "JANAVAAKYA – Voice of the People"
replace_text = "JANAVAAKYA – Voice of the People"
search_brand_html = '<img src="/static/img/janavaakya_logo.png" alt="JANAVAAKYA Logo" style="height:40px; vertical-align:middle;">'
replace_brand_html = '<img src="/static/img/janavaakya_logo.png" alt="JANAVAAKYA Logo" style="height:40px; vertical-align:middle;">'

modified_files = []

for dp, d_names, f_names in os.walk(ROOT_DIR):
    if 'node_modules' in dp or '.git' in dp or '__pycache__' in dp or 'venv' in dp:
        continue
    for f in f_names:
        if f.endswith(('.html', '.js', '.py', '.txt', '.md', '.json', '.jny', '.js', '.css', '.spec.js', '.js')):
            filepath = os.path.join(dp, f)
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                original_content = content
                
                # Replace exact text
                if search_text in content:
                    content = content.replace(search_text, replace_text)
                
                # Replace the HTML logo brand in templates 
                if search_brand_html in content:
                    content = content.replace(search_brand_html, replace_brand_html)
                    
                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as file:
                        file.write(content)
                    modified_files.append(filepath)
            except Exception as e:
                pass

print(f"Modified {len(modified_files)} files:")
for m in modified_files:
    print(f"- {os.path.relpath(m, ROOT_DIR)}")
