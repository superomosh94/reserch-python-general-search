import os
import json
import threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from reserch import GeneralResearchAutomator
from view_results_html import generate_html_report
from dashboard_generator import update_index

app = Flask(__name__)
CORS(app)

# Configuration
RESEARCH_DIR = "researches"
if not os.path.exists(RESEARCH_DIR):
    os.makedirs(RESEARCH_DIR)

# Thread-safe queue for progress updates
from queue import Queue
status_queues = {} # Topic -> Queue

@app.route('/')
def index_route():
    return send_from_directory(RESEARCH_DIR, 'index.html')

@app.route('/researches/<path:filename>')
def serve_research(filename):
    full_path = os.path.join(RESEARCH_DIR, filename)
    if os.path.isdir(full_path):
        # Generate a simple directory listing if it's a folder
        files = os.listdir(full_path)
        
        links = []
        for f in files:
            # Handle trailing slash logic for links
            base_url = f"/researches/{filename}"
            if not base_url.endswith('/'):
                base_url += "/"
            links.append(f'<li style="margin: 10px 0;"><a href="{base_url}{f}" style="color: #2563eb; text-decoration: none; font-size: 1.1rem; font-family: sans-serif;">📄 {f}</a></li>')
            
        links_html = "\n".join(links)
        html = f"""
        <html><body style="padding: 40px; background: #f8fafc;">
            <h2 style="font-family: sans-serif; color: #1e293b;">Directory listing for: {filename}</h2>
            <ul style="list-style: none; padding: 0;">{links_html}</ul>
            <br><a href="/" style="font-family: sans-serif; color: #64748b; text-decoration: none;">&larr; Back to Dashboard</a>
        </body></html>
        """
        return html
        
    return send_from_directory(RESEARCH_DIR, filename)

@app.route('/api/research/stream')
def stream():
    def event_stream():
        q = Queue()
        # Associate this stream with the latest research (simplified)
        # In a multi-user app we'd need a research ID
        status_queues['latest'] = q
        while True:
            msg = q.get()
            yield f"data: {json.dumps({'message': msg})}\n\n"
            if "complete" in msg.lower() or "error" in msg.lower():
                break
    return app.response_class(event_stream(), mimetype='text/event-stream')

@app.route('/api/research/run', methods=['POST'])
def run_research():
    data = request.json
    topic = data.get('topic')
    tool = data.get('tool') # 'smart', 'playwright', 'selenium', 'bs4'
    max_results = data.get('max_results', 15)
    
    if not topic:
        return jsonify({"error": "Topic is required"}), 400
        
    # Start research in a background thread
    thread = threading.Thread(target=perform_research_task, args=(topic, tool, max_results))
    thread.start()
    
    return jsonify({"message": "Research started", "topic": topic}), 202

def perform_research_task(topic, tool, max_results):
    def update_status(msg):
        print(f"STATUS: {msg}")
        if 'latest' in status_queues:
            status_queues['latest'].put(msg)

    try:
        update_status(f"Initializing research for: {topic}...")
        researcher = GeneralResearchAutomator(status_callback=update_status)
        
        # Tool preference mapping
        tool_preference = None if tool == 'smart' else tool
        
        # Run research
        data = researcher.research(topic, max_results, tool_preference)
        
        # Save results
        if sum(len(items) for items in data['sources'].values()) > 0:
            update_status("Saving reports and indexing...")
            txt_file = researcher.save_report()
            json_file = researcher.save_json_data()
            md_file = researcher.save_markdown_report()
            html_file = generate_html_report(json_file, researcher.research_dir)
            
            # Update central index and dashboard
            metadata = {
                "stats": {
                    "sources": sum(len(items) for items in data['sources'].values()),
                    "key_points": len(data.get('key_points', [])),
                    "trends": len(data.get('trends', []))
                },
                "files": [
                    {"name": "HTML Report", "path": html_file},
                    {"name": "Text Report", "path": txt_file},
                    {"name": "JSON Data", "path": json_file},
                    {"name": "Markdown Report", "path": md_file}
                ]
            }
            update_index(topic, researcher.research_dir, metadata)
            update_status("✅ Research completed successfully!")
        else:
            update_status("⚠ Done, but no results were found.")
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        print(error_msg)
        update_status(error_msg)

@app.route('/api/researches', methods=['GET'])
def list_researches():
    index_path = os.path.join(RESEARCH_DIR, "research_index.json")
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify([])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
