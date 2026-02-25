"""
Create an HTML viewer for research results
"""

import json
import os
import webbrowser
from datetime import datetime

def generate_html_report(json_data_path: str, output_dir: str = "."):
    """Generate an HTML report from JSON data and save it to the specified directory."""
    
    if not os.path.exists(json_data_path):
        print(f"Error: JSON data file not found at {json_data_path}")
        return None
        
    with open(json_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract sources for display
    sources = data.get('sources', {})
    all_items = []
    for cat, items in sources.items():
        for item in items:
            item['category'] = cat
            all_items.append(item)
            
    # Premium CSS
    css = """
    :root {
        --primary: #2563eb;
        --secondary: #1e40af;
        --bg: #f8fafc;
        --card: #ffffff;
        --text: #1e293b;
        --text-light: #64748b;
        --success: #10b981;
    }
    body { font-family: 'Inter', system-ui, -apple-system, sans-serif; margin: 0; background: var(--bg); color: var(--text); line-height: 1.5; }
    .container { max-width: 1000px; margin: 40px auto; padding: 0 20px; }
    .header { background: white; padding: 40px; border-radius: 16px; border: 1px solid #e2e8f0; margin-bottom: 30px; }
    h1 { margin: 0; color: var(--primary); font-size: 2.25rem; }
    .meta { color: var(--text-light); margin-top: 10px; font-size: 0.9rem; }
    
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }
    .stat-card { background: white; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center; }
    .stat-value { font-size: 2rem; font-weight: 700; color: var(--primary); display: block; }
    .stat-label { color: var(--text-light); font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; }
    
    .section { margin-bottom: 50px; }
    h2 { border-bottom: 2px solid var(--primary); display: inline-block; padding-bottom: 5px; margin-bottom: 25px; }
    
    .finding-item { background: white; padding: 20px; border-radius: 10px; border-left: 4px solid var(--success); margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    
    .source-card { background: white; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; transition: transform 0.2s; }
    .source-card:hover { transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .source-title { margin: 0 0 10px 0; font-size: 1.25rem; }
    .source-title a { color: var(--text); text-decoration: none; }
    .source-title a:hover { color: var(--primary); }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; background: #f1f5f9; color: var(--text-light); margin-bottom: 10px; }
    .source-summary { color: var(--text-light); font-size: 0.95rem; }
    """

    findings_html = "".join(f'<div class="finding-item">{f}</div>' for f in data.get('key_findings', [])[:15])
    
    sources_html = ""
    for item in all_items[:30]:
        title = item.get('title', 'N/A')
        url = item.get('url', item.get('link', '#'))
        summary = item.get('summary', '') or item.get('description', '')
        category = item.get('category', 'General')
        sources_html += f"""
        <div class="source-card">
            <span class="badge">{category}</span>
            <h3 class="source-title"><a href="{url}" target="_blank">{title}</a></h3>
            <p class="source-summary">{summary[:400]}{'...' if len(summary) > 400 else ''}</p>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Research: {data['query']}</title>
        <style>{css}</style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{data['query']}</h1>
                <div class="meta">Research Report • Generated on {data.get('timestamp', 'N/A')}</div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="stat-value">{len(all_items)}</span>
                    <span class="stat-label">Total Sources</span>
                </div>
                <div class="stat-card">
                    <span class="stat-value">{len(data.get('key_findings', []))}</span>
                    <span class="stat-label">Key Points</span>
                </div>
                <div class="stat-card">
                    <span class="stat-value">{len(data.get('definitions', []))}</span>
                    <span class="stat-label">Definitions</span>
                </div>
                <div class="stat-card">
                    <span class="stat-value">{len(data.get('trends', []))}</span>
                    <span class="stat-label">Trends</span>
                </div>
            </div>
            
            <div class="section">
                <h2>Key Findings</h2>
                {findings_html if findings_html else '<p>No specific findings extracted.</p>'}
            </div>
            
            <div class="section">
                <h2>Top Sources</h2>
                {sources_html if sources_html else '<p>No sources found.</p>'}
            </div>
        </div>
    </body>
    </html>
    """
    
    output_path = os.path.join(output_dir, "report.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_path

if __name__ == "__main__":
    # Compatibility with old usage
    import glob
    files = glob.glob("research_data_*.json")
    if files:
        latest = max(files, key=lambda f: os.path.getctime(f))
        path = generate_html_report(latest)
        if path:
            webbrowser.open(f"file:///{os.path.abspath(path)}")
    else:
        print("No research data found in current directory.")