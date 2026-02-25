import json

file_path = r'C:\Users\ADMIN\Documents\reserch-python\researches\ai_impact_on_software_development_2026_20260225_171044\data.json'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Topic: {data.get('query')}")
metrics = ['key_points', 'statistics', 'quotes', 'trends', 'definitions', 'case_studies']
for m in metrics:
    print(f"{m.replace('_', ' ').title()}: {len(data.get(m, []))}")

print("\n--- Sample Key Points ---")
for i, p in enumerate(data.get('key_points', [])[:3], 1):
    print(f"{i}. {p}")
