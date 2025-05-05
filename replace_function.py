import re

# Read fixed function
with open('fixed_function.py', 'r', encoding='utf-8') as f:
    fixed_function = f.read()

# Read app.py content
with open('app.py', 'r', encoding='utf-8') as f:
    app_content = f.read()

# Define pattern to find the get_person_for_week function
pattern = r'def get_person_for_week\(week_offset=0\):.*?return \{.*?\n    \}'

# Replace the function in app_content
updated_content = re.sub(pattern, fixed_function, app_content, flags=re.DOTALL)

# Write back to app.py
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(updated_content)

print("Function replacement complete!")
