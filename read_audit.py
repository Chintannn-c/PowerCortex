import json

with open('c:/Flutter/guvnl_project/audit_report.json', 'r') as f:
    d = json.load(f)

print("Backend Issues:")
for issue in d.get('backend', []):
    print(f" - {issue['category']}: {issue['file']} ({issue['type']})")

print("\nFrontend Issues:")
for issue in d.get('frontend', []):
    print(f" - {issue['category']}: {issue['file']} ({issue['type']})")
