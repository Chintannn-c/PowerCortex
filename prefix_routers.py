import glob
import os

for root, dirs, files in os.walk('lib'):
    for file in files:
        if file.endswith('.dart'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            if '/api/' in content:
                content = content.replace('/api/', '/api/v1/')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
print("Done")
