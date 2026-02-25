"""
Research Results Viewer
Run this after your research to view results in different ways
"""

import json
import os
import glob
from datetime import datetime

def find_latest_file(pattern):
    """Find the most recent file matching pattern"""
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def view_text_report():
    """View the most recent text report"""
    latest = find_latest_file("research_report_*.txt")
    if not latest:
        print("No research report found!")
        return
    
    print(f"\n{'='*60}")
    print(f"VIEWING: {latest}")
    print(f"{'='*60}\n")
    
    with open(latest, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content[:2000])  # Show first 2000 chars
        if len(content) > 2000:
            print("\n... (content truncated)")
    
    print(f"\nFull report saved at: {latest}")

def view_json_data():
    """View the most recent JSON data"""
    latest = find_latest_file("research_data_*.json")
    if not latest:
        print("No JSON data found!")
        return
    
    print(f"\n{'='*60}")
    print(f"LOADING: {latest}")
    print(f"{'='*60}\n")
    
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Display summary
    print(f"Topic: {data.get('query', 'N/A')}")
    print(f"Date: {data.get('timestamp', 'N/A')}")
    print(f"Total papers: {len(data.get('papers', []))}")
    print(f"Search terms: {len(data.get('expanded_terms', []))}")
    print(f"Key findings: {len(data.get('key_findings', []))}")
    print(f"Methodologies: {len(data.get('methodologies', []))}")
    
    # Show sample papers
    print(f"\n{'='*60}")
    print("SAMPLE PAPERS (first 5):")
    print(f"{'='*60}")
    for i, paper in enumerate(data.get('papers', [])[:5], 1):
        print(f"\n{i}. {paper.get('title', 'N/A')}")
        print(f"   Authors: {', '.join(paper.get('authors', ['N/A'])[:2])}")
        print(f"   Year: {paper.get('published', paper.get('year', 'N/A'))}")
        print(f"   Source: {paper.get('source', 'N/A')}")

def search_papers(keyword):
    """Search within the papers"""
    latest = find_latest_file("research_data_*.json")
    if not latest:
        print("No JSON data found!")
        return
    
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n{'='*60}")
    print(f"SEARCHING FOR: '{keyword}'")
    print(f"{'='*60}\n")
    
    matches = []
    for paper in data.get('papers', []):
        title = paper.get('title', '').lower()
        summary = paper.get('summary', '').lower()
        if keyword.lower() in title or keyword.lower() in summary:
            matches.append(paper)
    
    print(f"Found {len(matches)} matching papers:\n")
    for i, paper in enumerate(matches[:10], 1):
        print(f"{i}. {paper.get('title', 'N/A')}")
        print(f"   Year: {paper.get('published', paper.get('year', 'N/A'))}")
        print(f"   URL: {paper.get('url', 'N/A')}\n")

def export_to_csv():
    """Export papers to CSV for Excel"""
    latest = find_latest_file("research_data_*.json")
    if not latest:
        print("No JSON data found!")
        return
    
    import csv
    
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    csv_file = f"research_papers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['Title', 'Authors', 'Year', 'Source', 'Citations', 'URL', 'Summary'])
        
        # Write papers
        for paper in data.get('papers', []):
            writer.writerow([
                paper.get('title', 'N/A'),
                ', '.join(paper.get('authors', [])[:3]),
                paper.get('published', paper.get('year', 'N/A')),
                paper.get('source', 'N/A'),
                paper.get('citations', 0),
                paper.get('url', 'N/A'),
                paper.get('summary', '')[:200] + '...'
            ])
    
    print(f"✅ Exported to: {csv_file}")
    print("You can open this in Excel!")

def main():
    while True:
        print("\n" + "="*50)
        print("RESEARCH RESULTS VIEWER")
        print("="*50)
        print("1. View text report")
        print("2. View JSON summary")
        print("3. Search papers by keyword")
        print("4. Export to CSV (for Excel)")
        print("5. List all result files")
        print("6. Exit")
        
        choice = input("\nChoice (1-6): ").strip()
        
        if choice == '1':
            view_text_report()
        elif choice == '2':
            view_json_data()
        elif choice == '3':
            keyword = input("Enter search keyword: ").strip()
            search_papers(keyword)
        elif choice == '4':
            export_to_csv()
        elif choice == '5':
            print("\nResearch files found:")
            for f in glob.glob("research_*"):
                size = os.path.getsize(f)
                modified = datetime.fromtimestamp(os.path.getmtime(f))
                print(f"  • {f} ({size:,} bytes) - {modified}")
        elif choice == '6':
            break
        else:
            print("Invalid choice!")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()