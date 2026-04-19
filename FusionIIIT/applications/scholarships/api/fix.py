import re
with open('urls.py', 'r', encoding='utf-8') as f:
    text = f.read()
# fix duplicates
cleaned = []
for line in text.splitlines():
    if line not in cleaned:
        cleaned.append(line)
    elif 'path(' not in line and ']' not in line:
        cleaned.append(line)
with open('urls.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(cleaned))
