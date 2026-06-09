import os
import json
import ast
import re

def audit_python_file(filepath):
    issues = []
    ghost_data_keywords = ['dummy_data', 'fake_data', 'mock_data', 'hardcoded_fallback']
    security_keywords = ['jwt_secret', 'api_key', 'db_password', 'secret_key', 'auth_token']

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
            
        tree = ast.parse(source)
        lines = source.splitlines()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name_lower = target.id.lower()
                        if any(kw in name_lower for kw in security_keywords):
                            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                                val = node.value.value
                                if len(val) > 3 and val not in ['TODO', 'FIXME']:
                                    issues.append({
                                        'type': 'Security',
                                        'line': node.lineno,
                                        'severity': 'Critical',
                                        'issue': f"Hardcoded secret string assigned to variable '{target.id}'",
                                        'fix': 'Move to environment variables.'
                                    })
            
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                val_lower = node.value.lower()
                if len(val_lower) < 50:
                    for kw in ghost_data_keywords:
                        if kw in val_lower and 'error' not in val_lower and 'log' not in val_lower:
                            if 'logging' not in lines[node.lineno - 1] and 'logger' not in lines[node.lineno - 1]:
                                issues.append({
                                    'type': 'Ghost Data',
                                    'line': node.lineno,
                                    'severity': 'Medium',
                                    'issue': f"Ghost data string literal found: '{node.value}'",
                                    'fix': 'Remove dummy data from production codebase.'
                                })
            
            if isinstance(node, ast.ExceptHandler):
                if node.type is None or (isinstance(node.type, ast.Name) and node.type.id == 'Exception'):
                    for body_node in node.body:
                        if isinstance(body_node, ast.Pass):
                            issues.append({
                                'type': 'Bug',
                                'line': body_node.lineno,
                                'severity': 'High',
                                'issue': 'Silenced broad exception with pass',
                                'fix': 'Properly log or handle the exception.'
                            })

    except Exception:
        pass
    
    return issues

def audit_dart_file(filepath):
    issues = []
    ghost_data_keywords = ['dummy_data', 'fake_data', 'mock_data', 'hardcoded_fallback']
    security_keywords = ['jwt_secret', 'api_key', 'db_password', 'secret_key', 'auth_token']
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            line_str = line.strip()
            if line_str.startswith('//'):
                continue
                
            line_lower = line_str.lower()
            
            if '=' in line_str and not 'String.fromEnvironment' in line_str:
                left_side = line_str.split('=')[0].lower()
                if any(kw in left_side for kw in security_keywords):
                    if re.search(r'=\s*["\'][^"\']+["\']', line_str):
                        issues.append({
                            'type': 'Security',
                            'line': i + 1,
                            'severity': 'Critical',
                            'issue': f"Potential hardcoded secret assigned",
                            'fix': 'Move to environment variables.'
                        })
            
            string_literals = re.findall(r'["\']([^"\']+)["\']', line_str)
            for literal in string_literals:
                lit_lower = literal.lower()
                if any(kw in lit_lower for kw in ghost_data_keywords) and len(lit_lower) < 50:
                    if 'log' not in line_lower and 'print' not in line_lower:
                        issues.append({
                            'type': 'Ghost Data',
                            'line': i + 1,
                            'severity': 'Medium',
                            'issue': f"Ghost data string literal found: '{literal}'",
                            'fix': 'Remove dummy data from production codebase.'
                        })

    except Exception:
        pass
        
    return issues

def main():
    results = []
    
    backend_dir = 'c:\\Flutter\\guvnl_project\\backend\\app'
    for root, _, files in os.walk(backend_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                issues = audit_python_file(filepath)
                if issues:
                    results.append({'file': filepath, 'name': file, 'issues': issues})
                    
    frontend_dir = 'c:\\Flutter\\guvnl_project\\lib'
    for root, _, files in os.walk(frontend_dir):
        for file in files:
            if file.endswith('.dart'):
                filepath = os.path.join(root, file)
                issues = audit_dart_file(filepath)
                if issues:
                    results.append({'file': filepath, 'name': file, 'issues': issues})

    report = {
        'backend': [r for r in results if r['file'].endswith('.py')],
        'frontend': [r for r in results if r['file'].endswith('.dart')]
    }

    with open('c:\\Flutter\\guvnl_project\\audit_report.json', 'w') as f:
        json.dump(report, f, indent=4)

if __name__ == "__main__":
    main()
