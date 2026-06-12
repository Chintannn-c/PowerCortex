import json
import os

with open('bandit_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

for res in report.get('results', []):
    if res['issue_severity'] in ('HIGH', 'MEDIUM'):
        print(f"[{res['issue_severity']}] {res['issue_text']} | {res['filename']}:{res['line_number']}")
