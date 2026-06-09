import os
import re
import json

def audit_directory(dir_path, extensions):
    results = []
    ghost_data_keywords = ['seed', 'mock', 'dummy', 'sample', 'random', 'generated', 'fallback', 'heuristic', 'fake']
    security_keywords = ['password', 'secret', 'token', 'key', 'jwt_secret', 'api_key', 'http://']
    
    for root, _, files in os.walk(dir_path):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    file_issues = []
                    
                    for i, line in enumerate(lines):
                        line_lower = line.lower()
                        
                        # Check for ghost data
                        for kw in ghost_data_keywords:
                            if kw in line_lower:
                                file_issues.append({
                                    'type': 'Ghost Data',
                                    'line': i + 1,
                                    'severity': 'Medium',
                                    'issue': f"Found ghost data keyword: '{kw}'",
                                    'fix': 'Verify if this is used in production. Remove or replace with real data sources.'
                                })
                        
                        # Check for security
                        for kw in security_keywords:
                            if kw in line_lower and ('=' in line or ':' in line) and not 'import' in line_lower:
                                # Skip dynamic lookups
                                if 'os.getenv' in line or 'String.fromEnvironment' in line:
                                    continue
                                # Check if it's a hardcoded string literal assignment
                                # Matches var="string" or 'string'
                                if re.search(r'["\'][^"\']+["\']', line.split('=')[-1] if '=' in line else line.split(':')[-1]):
                                    file_issues.append({
                                        'type': 'Security',
                                        'line': i + 1,
                                        'severity': 'Critical',
                                        'issue': f"Potential hardcoded secret or unsecured HTTP: '{kw}'",
                                        'fix': 'Move to environment variables or secure vault. Use HTTPS.'
                                    })
                                
                        # Check for Python specific
                        if file.endswith('.py'):
                            if 'pass' in line and 'except' in lines[i-1]:
                                file_issues.append({
                                    'type': 'Bug',
                                    'line': i + 1,
                                    'severity': 'High',
                                    'issue': 'Silenced exception with pass',
                                    'fix': 'Properly log or handle the exception.'
                                })
                            if 'TODO' in line or 'FIXME' in line:
                                file_issues.append({
                                    'type': 'Missing Feature',
                                    'line': i + 1,
                                    'severity': 'Low',
                                    'issue': 'Incomplete implementation',
                                    'fix': 'Complete the TODO/FIXME.'
                                })
                            if re.search(r'\bprint\(', line_lower):
                                file_issues.append({
                                    'type': 'Performance/Bug',
                                    'line': i + 1,
                                    'severity': 'Low',
                                    'issue': 'Print statement left in code',
                                    'fix': 'Use proper logging mechanism instead.'
                                })

                        # Check for Dart specific
                        if file.endswith('.dart'):
                            if re.search(r'\bprint\(', line_lower):
                                file_issues.append({
                                    'type': 'Performance/Bug',
                                    'line': i + 1,
                                    'severity': 'Low',
                                    'issue': 'Print statement left in code',
                                    'fix': 'Use debugPrint or a logging library.'
                                })
                            if 'TODO' in line or 'FIXME' in line:
                                file_issues.append({
                                    'type': 'Missing Feature',
                                    'line': i + 1,
                                    'severity': 'Low',
                                    'issue': 'Incomplete implementation',
                                    'fix': 'Complete the TODO/FIXME.'
                                })
                                
                    if file_issues:
                        results.append({
                            'file': filepath,
                            'name': file,
                            'issues': file_issues
                        })
                except Exception as e:
                    pass
    return results

backend_issues = audit_directory('c:\\Flutter\\guvnl_project\\backend\\app', ['.py'])
frontend_issues = audit_directory('c:\\Flutter\\guvnl_project\\lib', ['.dart'])

report = {
    'backend': backend_issues,
    'frontend': frontend_issues
}

with open('c:\\Flutter\\guvnl_project\\audit_report.json', 'w') as f:
    json.dump(report, f, indent=4)
