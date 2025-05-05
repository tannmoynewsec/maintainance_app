import re

# Read app.py.bak content (the original file)
with open('app.py.bak', 'r', encoding='utf-8') as f:
    app_content = f.read()

# Make manual replacements to fix the issues
app_content = app_content.replace(
    'if date_str not in holidays:',
    'if date_str not in holiday_dates:'
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_content)

print("App.py restored with holiday_dates fix!")
