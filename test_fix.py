
import os
import json
from dashboard_generator import generate_dashboard
from view_results_html import generate_html_report

test_data = {
    "query": "test topic",
    "timestamp": "2026-02-25T16:00:00",
    "sources": {"web": [{"title": "Test", "url": "http://example.com", "summary": "margin test"}]},
    "key_findings": ["First finding", "Second finding"],
    "definitions": [],
    "trends": []
}

# Create a dummy json file
with open("test_data.json", "w") as f:
    json.dump(test_data, f)

print("Testing generate_html_report...")
try:
    generate_html_report("test_data.json", ".")
    print("✓ generate_html_report passed")
except Exception as e:
    print(f"✗ generate_html_report failed: {e}")

print("\nTesting generate_dashboard...")
try:
    generate_dashboard([{"topic": "test", "path": ".", "stats": {"sources": 1, "key_points": 2, "trends": 0}, "files": []}])
    print("✓ generate_dashboard passed")
except Exception as e:
    print(f"✗ generate_dashboard failed: {e}")
