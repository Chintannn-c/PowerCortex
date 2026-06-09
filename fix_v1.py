import glob
import os
import re

for f in glob.glob('backend/app/routers/*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    # Replace multiple /v1/v1/ with just /v1/
    content = re.sub(r'/api/(v1/)+', '/api/v1/', content)
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

for root, dirs, files in os.walk('lib'):
    for file in files:
        if file.endswith('.dart'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            # Replace multiple /v1/v1/ with just /v1/
            content = re.sub(r'/api/(v1/)+', '/api/v1/', content)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

print("Double v1 fixed")
