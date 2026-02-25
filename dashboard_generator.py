import os
import json
from datetime import datetime
from typing import List, Dict, Any

INDEX_FILE = "researches/research_index.json"
DASHBOARD_FILE = "researches/index.html"

def update_index(topic: str, research_dir: str, metadata: Dict[str, Any]):
    """Add or update an entry in the research index."""
    index_data = []
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
        except:
            index_data = []
            
    # Check if entry already exists (unlikely with timestamped dirs)
    new_entry = {
        "topic": topic,
        "path": research_dir,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": datetime.now().isoformat(),
        "stats": metadata.get("stats", {}),
        "files": metadata.get("files", [])
    }
    
    index_data.insert(0, new_entry) # Put newest first
    
    # Ensure researches directory exists
    os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
    
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2)
        
    generate_dashboard(index_data)

def generate_dashboard(index_data: List[Dict[str, Any]]):
    """Create a premium HTML dashboard to navigate researches."""
    
    rows = ""
    for entry in index_data:
        topic = entry.get("topic", "Unknown")
        date = entry.get("date", "N/A")
        stats = entry.get("stats", {})
        path = entry.get("path", "")
        
        # Relative path for the links in index.html (which is in researches/)
        # But for the Flask server, we need to prefix with /researches/
        rel_path = os.path.basename(path)
        server_path = f"/researches/{rel_path}"
        
        # Find available files in that directory
        files_links = ""
        for file_info in entry.get("files", []):
            name = file_info.get("name", "File")
            f_path = file_info.get("path", "")
            # Assume file is inside rel_path
            f_rel = os.path.basename(f_path)
            files_links += f'<a href="{server_path}/{f_rel}" target="_blank" class="file-link">{name}</a> '

        rows += f"""
        <div class="research-card">
            <div class="card-header">
                <h3>{topic}</h3>
                <span class="date">{date}</span>
            </div>
            <div class="card-stats">
                <span>📊 {stats.get('sources', 0)} Sources</span>
                <span>🔑 {stats.get('key_points', 0)} Key Points</span>
                <span>📈 {stats.get('trends', 0)} Trends</span>
            </div>
            <div class="card-actions">
                {files_links}
                <a href="{server_path}/" class="btn">Open Folder</a>
            </div>
        </div>
        """

    controls = """
    <div class="controls-card">
        <h2>🚀 Start New Research</h2>
        <div class="form-grid">
            <div class="input-group">
                <label for="topic">Research Topic</label>
                <input type="text" id="topic" placeholder="e.g., Quantum Computing Trends">
            </div>
            <div class="input-group">
                <label for="tool">Scraping Model</label>
                <select id="tool">
                    <option value="smart">Smart (Auto-detect)</option>
                    <option value="playwright">Playwright (JS-heavy)</option>
                    <option value="selenium">Selenium (Interactive)</option>
                    <option value="bs4">Static (Fast)</option>
                </select>
            </div>
            <button onclick="startResearch()" id="startBtn">Start Research</button>
        </div>
        
        <div id="progressContainer" class="progress-container" style="display: none;">
            <div class="progress-bar-bg">
                <div id="progressBar" class="progress-bar"></div>
            </div>
            <div id="statusMessage" class="status-message">Initializing...</div>
            <div id="logWindow" class="log-window"></div>
        </div>
    </div>
    """

    js = """
    let eventSource = null;

    function startResearch() {
        const topic = document.getElementById('topic').value;
        const tool = document.getElementById('tool').value;
        const btn = document.getElementById('startBtn');
        const progressContainer = document.getElementById('progressContainer');
        const status = document.getElementById('statusMessage');
        const log = document.getElementById('logWindow');
        const bar = document.getElementById('progressBar');
        
        if (!topic) {
            alert('Please enter a topic');
            return;
        }
        
        // Reset UI
        btn.disabled = true;
        btn.innerText = 'Running...';
        progressContainer.style.display = 'block';
        log.innerHTML = '';
        bar.style.width = '5%';
        status.innerText = 'Connecting to research stream...';
        
        // Connect to SSE
        if (eventSource) eventSource.close();
        eventSource = new EventSource('/api/research/stream');
        
        eventSource.onmessage = function(e) {
            const data = JSON.parse(e.data);
            const msg = data.message;
            
            // Add to log
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            logEntry.innerText = `[${new Date().toLocaleTimeString()}] ${msg}`;
            log.prepend(logEntry);
            
            status.innerText = msg;
            
            // Basic progress bar logic
            if (msg.includes('Generating')) bar.style.width = '15%';
            else if (msg.includes('Wikipedia')) bar.style.width = '30%';
            else if (msg.includes('Phase 1')) bar.style.width = '40%';
            else if (msg.includes('Phase 2')) bar.style.width = '50%';
            else if (msg.includes('Phase 3')) bar.style.width = '60%';
            else if (msg.includes('Phase 4')) bar.style.width = '70%';
            else if (msg.includes('Phase 5')) bar.style.width = '80%';
            else if (msg.includes('Deep diving')) bar.style.width = '85%';
            else if (msg.includes('Saving')) bar.style.width = '90%';
            else if (msg.includes('✅')) {
                bar.style.width = '100%';
                bar.style.backgroundColor = 'var(--success)';
                btn.disabled = false;
                btn.innerText = 'Start Research';
                eventSource.close();
                // Refresh dashboard list after a delay
                setTimeout(() => location.reload(), 2000);
            }
            else if (msg.includes('❌')) {
                bar.style.backgroundColor = 'var(--error)';
                btn.disabled = false;
                btn.innerText = 'Start Research';
                eventSource.close();
            }
        };
        
        eventSource.onerror = function() {
            console.error('SSE Error');
            eventSource.close();
        };

        // Start research
        fetch('/api/research/run', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({topic, tool})
        }).catch(err => {
            status.innerText = 'Error starting research';
            btn.disabled = false;
        });
    }
    """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Research Hub Dashboard</title>
        <style>
            :root {{
                --primary: #2563eb;
                --primary-hover: #1d4ed8;
                --bg: #f8fafc;
                --card-bg: #ffffff;
                --text: #1e293b;
                --text-light: #64748b;
                --border: #e2e8f0;
                --success: #10b981;
                --error: #ef4444;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: var(--bg);
                color: var(--text);
                margin: 0;
                padding: 40px;
                line-height: 1.6;
            }}
            .container {{
                max-width: 1000px;
                margin: auto;
            }}
            header {{
                margin-bottom: 40px;
                text-align: center;
            }}
            h1 {{
                font-size: 2.5rem;
                margin-bottom: 10px;
                background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            .subtitle {{ color: var(--text-light); }}
            
            .controls-card {{
                background: var(--card-bg);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 30px;
                margin-bottom: 40px;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            }}
            .controls-card h2 {{ margin-top: 0; margin-bottom: 20px; font-size: 1.5rem; }}
            .form-grid {{
                display: grid;
                grid-template-columns: 2fr 1fr auto;
                gap: 20px;
                align-items: flex-end;
            }}
            .input-group {{ display: flex; flex-direction: column; gap: 8px; }}
            label {{ font-size: 0.85rem; font-weight: 600; color: var(--text-light); text-transform: uppercase; }}
            input, select {{
                padding: 10px 12px;
                border: 1px solid var(--border);
                border-radius: 8px;
                font-size: 1rem;
                outline: none;
                transition: border-color 0.2s;
            }}
            input:focus, select:focus {{ border-color: var(--primary); }}
            
            #startBtn {{
                background: var(--primary);
                color: white;
                border: none;
                padding: 11px 25px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.2s;
            }}
            #startBtn:hover {{ background: var(--primary-hover); }}
            #startBtn:disabled {{ background: var(--text-light); cursor: not-allowed; }}
            
            .status-message {{ margin-top: 15px; font-size: 0.9rem; font-weight: 500; }}
            .status-message.success {{ color: var(--success); }}
            .status-message.error {{ color: var(--error); }}

            .progress-container {{
                margin-top: 30px;
                padding: 20px;
                background: #f1f5f9;
                border-radius: 12px;
                border: 1px solid var(--border);
            }}
            .progress-bar-bg {{
                background: #e2e8f0;
                height: 12px;
                border-radius: 6px;
                overflow: hidden;
                margin-bottom: 10px;
            }}
            .progress-bar {{
                background: var(--primary);
                height: 100%;
                width: 0%;
                transition: width 0.3s ease;
            }}
            .log-window {{
                margin-top: 15px;
                background: #1e293b;
                color: #f8fafc;
                font-family: 'Consolas', monospace;
                font-size: 0.8rem;
                padding: 15px;
                border-radius: 8px;
                height: 150px;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
            }}
            .log-entry {{
                margin-bottom: 5px;
                border-bottom: 1px solid #334155;
                padding-bottom: 5px;
            }}

            .dashboard-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
            }}
            
            .research-card {{
                background: var(--card-bg);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 20px;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .research-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
            }}
            
            .card-header {{
                display: flex;
                flex-direction: column;
                margin-bottom: 15px;
            }}
            .card-header h3 {{
                margin: 0;
                font-size: 1.2rem;
                color: var(--primary);
                word-break: break-all;
            }}
            .date {{ font-size: 0.75rem; color: var(--text-light); margin-top: 4px; }}
            
            .card-stats {{
                display: flex;
                gap: 12px;
                font-size: 0.85rem;
                margin-bottom: 20px;
                color: var(--text-light);
            }}
            
            .card-actions {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                border-top: 1px solid var(--border);
                padding-top: 15px;
            }}
            
            .file-link {{
                font-size: 0.8rem;
                text-decoration: none;
                color: var(--primary);
                background: #eff6ff;
                padding: 3px 8px;
                border-radius: 6px;
                border: 1px solid #dbeafe;
            }}
            .file-link:hover {{ background: #dbeafe; }}
            
            .btn {{
                margin-top: 10px;
                width: 100%;
                text-align: center;
                background: var(--primary);
                color: white;
                text-decoration: none;
                padding: 8px;
                border-radius: 8px;
                font-size: 0.85rem;
                font-weight: 500;
                display: block;
            }}
            
            .empty-state {{
                text-align: center;
                padding: 60px;
                background: var(--card-bg);
                border-radius: 12px;
                border: 2px dashed var(--border);
                grid-column: 1 / -1;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Research Hub</h1>
                <p class="subtitle">Premium Automated Research Interface</p>
            </header>
            
            {controls}
            
            <div class="dashboard-grid">
                {rows if rows else '<div class="empty-state"><h3>No research recorded yet</h3><p>Enter a topic above to start your first session.</p></div>'}
            </div>
        </div>
        <script>{js}</script>
    </body>
    </html>
    """
    
    with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Dashboard updated: {DASHBOARD_FILE}")

if __name__ == "__main__":
    # Test generation
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        generate_dashboard(data)
