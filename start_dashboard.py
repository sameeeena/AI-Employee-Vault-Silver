"""
Dashboard Web Server
Serves the attractive dashboard interface
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

PORT = 8080
BASE_DIR = Path(__file__).parent.absolute()


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)
    
    def log_message(self, format, *args):
        print(f"🌐 {args[0]}")


def start_server():
    os.chdir(BASE_DIR)
    
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print("\n" + "="*60)
        print("🚀 SILVER AI EMPLOYEE - DASHBOARD SERVER")
        print("="*60)
        print(f"\n📊 Dashboard URL: http://localhost:{PORT}/dashboard.html")
        print(f"📁 Serving from: {BASE_DIR}")
        print("\n" + "="*60)
        print("Press Ctrl+C to stop the server")
        print("="*60)
        
        # Auto-open browser
        webbrowser.open(f"http://localhost:{PORT}/dashboard.html")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Dashboard server stopped")
            httpd.shutdown()


if __name__ == "__main__":
    start_server()
