#!/usr/bin/env python3
"""
MCP Server for Silver AI Employee

Implements Model Context Protocol (MCP) server for external actions like sending emails.
Provides tools that can be called by AI agents.
"""

import os
import sys
import json
import logging
import smtplib
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configuration
DEFAULT_PORT = 8765

class MCPServer:
    """MCP Server providing tools for external actions."""

    def __init__(self, host: str = "localhost", port: int = DEFAULT_PORT):
        self.base_dir = Path(__file__).parent.absolute()
        self.host = host
        self.port = port
        self.logs_dir = self.base_dir / "logs"
        self.config_dir = self.base_dir / "mcp_config"
        
        # Ensure directories exist
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Load configuration
        self.config = self._load_config()
        
        # Registered tools
        self.tools: Dict[str, Dict] = {}
        self._register_default_tools()

    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = self.logs_dir / "mcp_server_log.md"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, mode='a', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _load_config(self) -> Dict:
        """Load MCP server configuration."""
        config_file = self.config_dir / "mcp_server_config.json"
        
        default_config = {
            "server_name": "Silver AI Employee MCP Server",
            "version": "1.0.0",
            "tools": [],
            "smtp": {
                "server": "smtp.gmail.com",
                "port": 587,
                "use_tls": True
            }
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    config.update(default_config)
                    return config
            except Exception as e:
                self.logger.warning(f"Could not load config: {e}")
        
        # Save default config
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config

    def _register_default_tools(self):
        """Register default tools."""
        
        # Tool 1: Send Email
        self.register_tool(
            name="send_email",
            description="Send an email via SMTP",
            parameters={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body content"},
                    "html": {"type": "boolean", "description": "Whether body is HTML", "default": False}
                },
                "required": ["to", "subject", "body"]
            },
            handler=self._send_email_handler
        )
        
        # Tool 2: Log Activity
        self.register_tool(
            name="log_activity",
            description="Log an activity to the system logs",
            parameters={
                "type": "object",
                "properties": {
                    "activity_type": {"type": "string", "description": "Type of activity"},
                    "description": {"type": "string", "description": "Activity description"},
                    "metadata": {"type": "object", "description": "Additional metadata"}
                },
                "required": ["activity_type", "description"]
            },
            handler=self._log_activity_handler
        )
        
        # Tool 3: Create Task
        self.register_tool(
            name="create_task",
            description="Create a new task in the Inbox",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title"},
                    "content": {"type": "string", "description": "Task content"},
                    "source": {"type": "string", "description": "Task source", "default": "mcp"},
                    "priority": {"type": "string", "description": "Task priority", "enum": ["low", "medium", "high", "critical"]}
                },
                "required": ["title", "content"]
            },
            handler=self._create_task_handler
        )
        
        # Tool 4: Get System Status
        self.register_tool(
            name="get_system_status",
            description="Get current system status and metrics",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            handler=self._get_system_status_handler
        )
        
        self.logger.info(f"✅ Registered {len(self.tools)} MCP tools")

    def register_tool(self, name: str, description: str, parameters: Dict, handler: callable):
        """Register a new tool."""
        self.tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler
        }
        self.logger.info(f"🔧 Registered tool: {name}")

    def _send_email_handler(self, params: Dict) -> Dict:
        """Handle send_email tool call."""
        try:
            to_email = params.get("to")
            subject = params.get("subject")
            body = params.get("body")
            is_html = params.get("html", False)
            
            # Get SMTP credentials from environment
            smtp_server = self.config.get("smtp", {}).get("server", "smtp.gmail.com")
            smtp_port = self.config.get("smtp", {}).get("port", 587)
            use_tls = self.config.get("smtp", {}).get("use_tls", True)
            
            sender_email = os.getenv("SMTP_USERNAME", os.getenv("SMTP_EMAIL", os.getenv("GMAIL_ADDRESS", "")))
            sender_password = os.getenv("SMTP_PASSWORD", "")
            
            if not sender_email or not sender_password:
                return {
                    "success": False,
                    "error": "SMTP credentials not configured. Set SMTP_EMAIL and SMTP_PASSWORD in .env"
                }
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender_email
            msg["To"] = to_email
            
            # Attach body
            mime_type = "html" if is_html else "plain"
            msg.attach(MIMEText(body, mime_type))
            
            # Send email
            if use_tls:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [to_email], msg.as_string())
            server.quit()
            
            self.logger.info(f"✅ Email sent to {to_email}: {subject}")
            
            return {
                "success": True,
                "message": f"Email sent to {to_email}",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _log_activity_handler(self, params: Dict) -> Dict:
        """Handle log_activity tool call."""
        try:
            activity_type = params.get("activity_type", "unknown")
            description = params.get("description", "")
            metadata = params.get("metadata", {})
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "activity_type": activity_type,
                "description": description,
                "metadata": metadata
            }
            
            # Append to MCP activities log
            activities_log = self.logs_dir / "mcp_activities.json"
            activities = []
            if activities_log.exists():
                try:
                    with open(activities_log, 'r') as f:
                        activities = json.load(f)
                except:
                    pass
            
            activities.append(log_entry)
            
            # Keep last 1000 entries
            activities = activities[-1000:]
            
            with open(activities_log, 'w') as f:
                json.dump(activities, f, indent=2)
            
            self.logger.info(f"📝 Activity logged: {activity_type}")
            
            return {
                "success": True,
                "message": "Activity logged successfully",
                "log_entry": log_entry
            }
            
        except Exception as e:
            self.logger.error(f"Failed to log activity: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _create_task_handler(self, params: Dict) -> Dict:
        """Handle create_task tool call."""
        try:
            title = params.get("title", "Untitled Task")
            content = params.get("content", "")
            source = params.get("source", "mcp")
            priority = params.get("priority", "medium")
            
            # Generate task ID
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            task_id = f"TSK-{timestamp}-mcp"
            
            # Create task content
            task_content = f"""# Task: {title}

**Task ID:** {task_id}
**Source:** {source}
**Priority:** {priority}
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Created via:** MCP Server

---

## Description

{content}

---

## Processing Status

- [ ] Classify task
- [ ] Prioritize task
- [ ] Execute required actions

---

*Created via MCP Server*
"""
            
            # Save task file
            inbox_dir = self.base_dir / "Inbox"
            inbox_dir.mkdir(parents=True, exist_ok=True)
            
            safe_title = "".join(c if c.isalnum() or c in ' -_' else '_' for c in title[:30])
            task_file = inbox_dir / f"{task_id}_mcp_{safe_title}.md"
            
            with open(task_file, 'w', encoding='utf-8') as f:
                f.write(task_content)
            
            self.logger.info(f"✅ Task created: {task_file.name}")
            
            return {
                "success": True,
                "message": "Task created successfully",
                "task_id": task_id,
                "task_file": str(task_file)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create task: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_system_status_handler(self, params: Dict) -> Dict:
        """Handle get_system_status tool call."""
        try:
            # Count files in directories
            inbox_count = len(list((self.base_dir / "Inbox").glob("*.md"))) if (self.base_dir / "Inbox").exists() else 0
            needs_action_count = len(list((self.base_dir / "Needs_Action").glob("*.md"))) if (self.base_dir / "Needs_Action").exists() else 0
            done_count = len(list((self.base_dir / "Done").glob("*.md"))) if (self.base_dir / "Done").exists() else 0
            plans_count = len(list((self.base_dir / "Plans").glob("*.md"))) if (self.base_dir / "Plans").exists() else 0
            
            status = {
                "timestamp": datetime.now().isoformat(),
                "server": {
                    "name": self.config.get("server_name"),
                    "version": self.config.get("version"),
                    "tools_registered": len(self.tools),
                    "tools": list(self.tools.keys())
                },
                "system": {
                    "inbox_tasks": inbox_count,
                    "needs_action_tasks": needs_action_count,
                    "completed_tasks": done_count,
                    "plans_created": plans_count
                }
            }
            
            return {
                "success": True,
                "status": status
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def call_tool(self, tool_name: str, params: Dict) -> Dict:
        """Call a registered tool."""
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}"
            }
        
        tool = self.tools[tool_name]
        handler = tool["handler"]
        
        self.logger.info(f"🔧 Calling tool: {tool_name}")
        return handler(params)

    def list_tools(self) -> List[Dict]:
        """List all registered tools."""
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
            for tool in self.tools.values()
        ]

    def get_tool_schema(self) -> Dict:
        """Get MCP server schema for external consumption."""
        return {
            "server_name": self.config.get("server_name"),
            "version": self.config.get("version"),
            "tools": self.list_tools()
        }

    def save_config(self):
        """Save current configuration."""
        config_file = self.config_dir / "mcp_server_config.json"
        config = {
            "server_name": self.config.get("server_name"),
            "version": self.config.get("version"),
            "tools": list(self.tools.keys()),
            "smtp": self.config.get("smtp", {})
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.logger.info(f"💾 Configuration saved to {config_file}")


def run_web_server():
    """Run MCP server with web interface for browser testing."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json as json_lib
    from urllib.parse import parse_qs, urlparse
    
    server = MCPServer()
    server.save_config()
    
    class MCPWebHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            """Handle GET requests - show web interface."""
            if self.path == '/' or self.path == '/index.html':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                html = f"""<!DOCTYPE html>
<html>
<head>
    <title>MCP Server - Silver AI Employee</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; }}
        h1 {{ color: #2563eb; }}
        .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .tool {{ background: #f3f4f6; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .success {{ color: #059669; }}
        .error {{ color: #dc2626; }}
        button {{ background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }}
        button:hover {{ background: #1d4ed8; }}
        input, textarea {{ width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }}
        textarea {{ height: 100px; }}
        .result {{ background: #1f2937; color: #10b981; padding: 15px; border-radius: 5px; margin-top: 10px; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <h1>🔌 MCP Server - Silver AI Employee</h1>
    
    <div class="card">
        <h2>Server Status</h2>
        <p><strong>Name:</strong> {server.config.get('server_name')}</p>
        <p><strong>Version:</strong> {server.config.get('version')}</p>
        <p><strong>Tools Available:</strong> {len(server.tools)}</p>
    </div>
    
    <div class="card">
        <h2>Available Tools</h2>
        {self._generate_tool_cards()}
    </div>
    
    <div class="card">
        <h2>Test Tool Call</h2>
        <form id="toolForm">
            <label><strong>Tool:</strong></label>
            <select id="toolSelect" onchange="updateParams()">
                <option value="get_system_status">get_system_status</option>
                <option value="create_task">create_task</option>
                <option value="log_activity">log_activity</option>
                <option value="send_email">send_email</option>
            </select>
            
            <label><strong>Parameters (JSON):</strong></label>
            <textarea id="params" name="params">{{}}</textarea>
            
            <button type="button" onclick="callTool()">Call Tool</button>
        </form>
        
        <div id="result" class="result" style="display:none;"></div>
    </div>
    
    <script>
        const paramExamples = {{
            get_system_status: '{{}}',
            create_task: '{{"title":"Test Task","content":"Testing MCP","priority":"low"}}',
            log_activity: '{{"activity_type":"test","description":"Testing MCP server"}}',
            send_email: '{{"to":"test@example.com","subject":"Test","body":"Hello"}}'
        }};
        
        function updateParams() {{
            const tool = document.getElementById('toolSelect').value;
            document.getElementById('params').value = paramExamples[tool];
        }}
        
        async function callTool() {{
            const tool = document.getElementById('toolSelect').value;
            const params = document.getElementById('params').value;
            const resultDiv = document.getElementById('result');
            
            try {{
                const response = await fetch('/api/call_tool', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{tool, params: JSON.parse(params)}})
                }});
                const result = await response.json();
                resultDiv.style.display = 'block';
                resultDiv.textContent = JSON.stringify(result, null, 2);
            }} catch (error) {{
                resultDiv.style.display = 'block';
                resultDiv.textContent = 'Error: ' + error.message;
            }}
        }}
        
        updateParams();
    </script>
</body>
</html>"""
                self.wfile.write(html.encode())
            
            elif self.path == '/api/tools':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                tools = server.list_tools()
                self.wfile.write(json_lib.dumps(tools, indent=2).encode())
            
            elif self.path == '/api/status':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                result = server.call_tool('get_system_status', {})
                self.wfile.write(json_lib.dumps(result, indent=2).encode())
            
            else:
                self.send_response(404)
                self.end_headers()
        
        def do_POST(self):
            """Handle POST requests - tool calls."""
            if self.path == '/api/call_tool':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json_lib.loads(post_data.decode())
                
                tool_name = data.get('tool')
                params = data.get('params', {})
                
                result = server.call_tool(tool_name, params)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json_lib.dumps(result, indent=2).encode())
            
            else:
                self.send_response(404)
                self.end_headers()
        
        def _generate_tool_cards(self):
            """Generate HTML cards for each tool."""
            html = ""
            for tool in server.tools.values():
                html += f"""
                <div class="tool">
                    <h3>{tool['name']}</h3>
                    <p>{tool['description']}</p>
                    <small>Parameters: {json_lib.dumps(tool['parameters'], indent=2)}</small>
                </div>
                """
            return html
        
        def log_message(self, format, *args):
            server.logger.info(f"Web request: {args[0]}")
    
    httpd = HTTPServer((server.host, server.port), MCPWebHandler)
    
    print("\n" + "="*60)
    print("🔌 MCP SERVER WITH WEB INTERFACE STARTED")
    print("="*60)
    print(f"Server: {server.config.get('server_name')}")
    print(f"Version: {server.config.get('version')}")
    print(f"Tools: {list(server.tools.keys())}")
    print("="*60)
    print(f"\n🌐 Open in browser: http://{server.host}:{server.port}")
    print("="*60)
    print("\nAPI Endpoints:")
    print(f"  GET  /              - Web interface")
    print(f"  GET  /api/tools     - List all tools")
    print(f"  GET  /api/status    - Get system status")
    print(f"  POST /api/call_tool - Call a tool")
    print("="*60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nMCP server stopped by user")
        httpd.shutdown()


def run_server():
    """Run MCP server (CLI mode)."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Server")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port")
    parser.add_argument("--web", action="store_true", help="Run with web interface")
    
    args = parser.parse_args()
    
    if args.web:
        run_web_server()
    else:
        server = MCPServer(host=args.host, port=args.port)
        server.save_config()
        
        print("\n" + "="*60)
        print("🔌 MCP SERVER STARTED")
        print("="*60)
        print(f"Server: {server.config.get('server_name')}")
        print(f"Version: {server.config.get('version')}")
        print(f"Tools: {list(server.tools.keys())}")
        print("="*60)
        print("\nUsage examples:")
        print("  from mcp_server import MCPServer")
        print("  server = MCPServer()")
        print("  result = server.call_tool('send_email', {'to': 'test@example.com', 'subject': 'Test', 'body': 'Hello'})")
        print("="*60)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nMCP server stopped by user")


# Simple CLI for testing
def cli_test():
    """Test MCP tools via CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Server CLI")
    parser.add_argument("tool", type=str, help="Tool name to call")
    parser.add_argument("--params", type=str, default="{}", help="JSON parameters")
    
    args = parser.parse_args()
    
    server = MCPServer()
    
    try:
        params = json.loads(args.params)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        return
    
    result = server.call_tool(args.tool, params)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    import time
    
    # Check if first argument is a tool name (CLI mode)
    if len(sys.argv) > 1 and sys.argv[1] not in ["--host", "--port", "--web", "-h", "--help"]:
        # CLI test mode - first arg is tool name
        server = MCPServer()
        tool_name = sys.argv[1]
        
        # Parse params from --params flag
        params = {}
        if "--params" in sys.argv:
            params_idx = sys.argv.index("--params")
            if params_idx + 1 < len(sys.argv):
                try:
                    params = json.loads(sys.argv[params_idx + 1])
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON: {e}")
                    sys.exit(1)
        
        result = server.call_tool(tool_name, params)
        print(json.dumps(result, indent=2))
    elif "--web" in sys.argv:
        run_web_server()
    else:
        run_server()
