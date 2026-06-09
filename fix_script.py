import os
import re

def fix_backend_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Fix print statements (simple heuristic: print( -> logger.info()
    if 'print(' in content:
        if 'import logging' not in content:
            content = 'import logging\nlogger = logging.getLogger(__name__)\n' + content
        content = re.sub(r'\bprint\(', 'logger.info(', content)

    # Fix exception passing
    content = re.sub(r'except\s+Exception(\s+as\s+\w+)?:[ \t]*\n[ \t]*pass', 
                     r'except Exception as e:\n            logger.error(f"Handled error: {e}")', content)

    # Fix Security Secrets (heuristic: replacing hardcoded secrets with os.getenv)
    # Be careful not to break settings.py or similar.
    content = re.sub(r'(jwt_secret|secret|api_key|password|token|key)\s*=\s*["\'][^"\']+["\']', 
                     r'\1 = os.getenv("\1".upper(), "")', content, flags=re.IGNORECASE)
                     
    # For model_loader.py fallbacks
    if "model_loader.py" in filepath:
        # Instead of returning mock data, raise ModelUnavailableError
        content = content.replace('SOURCE_HEURISTIC_FALLBACK', 'SOURCE_HEURISTIC_FALLBACK')
        # We'll manually fix complex python files if needed, but the script can do simple string replacements.

    if content != original:
        if 'os.getenv' in content and 'import os' not in content:
            content = 'import os\n' + content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def fix_frontend_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Fix print statements -> debugPrint
    if 'print(' in content:
        if "import 'package:flutter/foundation.dart';" not in content and "import 'package:flutter/material.dart';" not in content:
            content = "import 'package:flutter/foundation.dart';\n" + content
        content = re.sub(r'\bprint\(', 'debugPrint(', content)

    # Fix Security Secrets in Dart (replace string literals for keys with String.fromEnvironment)
    # Examples: 'your_api_key' -> const String.fromEnvironment('API_KEY')
    # This is a bit trickier with regex in Dart.
    # We will look for common pattern: token = "..."
    # Actually, let's just do a manual fix for the heavily impacted files (auth, api_client) to avoid breaking dart syntax.
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    project_path = r'c:\Flutter\guvnl_project'
    
    backend_path = os.path.join(project_path, 'backend', 'app')
    frontend_path = os.path.join(project_path, 'lib')
    
    fixed_backend = 0
    for root, _, files in os.walk(backend_path):
        for file in files:
            if file.endswith('.py'):
                if fix_backend_file(os.path.join(root, file)):
                    fixed_backend += 1
                    
    fixed_frontend = 0
    for root, _, files in os.walk(frontend_path):
        for file in files:
            if file.endswith('.dart'):
                if fix_frontend_file(os.path.join(root, file)):
                    fixed_frontend += 1
                    
    print(f"Fixed {fixed_backend} backend files and {fixed_frontend} frontend files.")

if __name__ == '__main__':
    main()
