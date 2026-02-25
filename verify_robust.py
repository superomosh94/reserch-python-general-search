import json
import os

file_path = r'C:\Users\ADMIN\Documents\reserch-python\researches\ai_impact_on_software_development_2026_20260225_171044\data.json'
output_path = r'C:\Users\ADMIN\Documents\reserch-python\verification_report.txt'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

with open(output_path, 'w', encoding='utf-8') as out:
    out.write(f"Topic: {data.get('query')}\n")
    out.write(f"Total Sources (Web): {len(data['sources']['web_results'])}\n")
    out.write(f"Total Sources (News): {len(data['sources']['news'])}\n")
    out.write(f"Total Deep Dive: {len(data['sources']['deep_dive'])}\n")
    
    metrics = ['key_points', 'statistics', 'quotes', 'trends', 'definitions', 'case_studies']
    for m in metrics:
        out.write(f"{m.replace('_', ' ').title()}: {len(data.get(m, []))}\n")
    
    out.write("\n--- Key Points Sample ---\n")
    for i, p in enumerate(data.get('key_points', [])[:5], 1):
        out.write(f"{i}. {p}\n")
    
    out.write("\n--- Statistics Sample ---\n")
    for i, p in enumerate(data.get('statistics', [])[:5], 1):
        out.write(f"{i}. {p}\n")

print(f"Report written to {output_path}")
