"""
Automated WhatsApp Sender with Task Tracking
Sends WhatsApp message AND creates task file that flows through: Inbox → Needs_Action → Done → Dashboard
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from whatsapp_automation import send_whatsapp_message

load_dotenv()

# Configuration
MY_WHATSAPP_NUMBER = os.getenv("MY_WHATSAPP_NUMBER", "")

# Project paths
BASE_DIR = Path(__file__).parent.absolute()
INBOX_DIR = BASE_DIR / "Inbox"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
INBOX_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def send_whatsapp_auto(to_number, message, project_name="AI Employee"):
    """
    Send WhatsApp message and create task file for tracking.
    
    Returns:
        tuple: (success: bool, task_id: str or None)
    """
    timestamp = datetime.now()
    task_id = f"TSK-{timestamp.strftime('%Y%m%d')}-{timestamp.strftime('%H%M%S')}"
    
    # Format message with project name
    full_message = f"*[{project_name}]* {message}"
    
    try:
        print("="*60)
        print("📱 AUTOMATED WHATSAPP WITH TASK TRACKING")
        print("="*60)
        print(f"To: {to_number}")
        print(f"Message: {message}")
        print(f"Project: {project_name}")
        print("="*60)
        print()
        
        # Step 1: Create task file in Inbox FIRST (before sending)
        print("📝 Creating task file...")
        task_content = create_task_file(
            to_number, 
            message, 
            full_message,
            task_id, 
            timestamp,
            project_name
        )
        print(f"✅ Task created: {task_id}")
        print(f"📂 File saved in Inbox/")
        print()
        
        # Step 2: Send the WhatsApp message
        print("📱 Sending WhatsApp message...")
        print("   (A browser window will open)")
        print("   (DO NOT touch anything - automation in progress)")
        print()
        
        success = send_whatsapp_message(to_number, full_message, wait_time=15)
        
        if success:
            print()
            print(f"✅ WhatsApp message sent successfully!")
            
            # Step 3: Update task file status
            update_task_status(task_id, "Sent")
            
            # Step 4: Log the action
            log_whatsapp_sent(task_id, to_number, message)
            
            print()
            print(f"📊 Task will flow: Inbox → Needs_Action → Done")
            print(f"📊 Dashboard will update automatically")
            
            return True, task_id
        else:
            print()
            print("❌ WhatsApp sending failed!")
            log_whatsapp_error(task_id, to_number, "Sending failed")
            return False, None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        log_whatsapp_error(task_id, to_number, str(e))
        return False, None


def create_task_file(to_number, message, full_message, task_id, timestamp, project_name):
    """Create a task file in Inbox directory."""
    
    task_content = f"""---
task_id: {task_id}
source: whatsapp
sender: {MY_WHATSAPP_NUMBER or 'Unknown'}
recipient: {to_number}
timestamp: {timestamp.isoformat()}
received_at: {timestamp.isoformat()}
subject: WhatsApp message to {to_number}
status: Inbox
priority: normal
tags: [whatsapp, sent, automated]
project_name: {project_name}
---

# WhatsApp Message Sent

## Details

| Field | Value |
|-------|-------|
| **To** | {to_number} |
| **From** | {MY_WHATSAPP_NUMBER or 'Unknown'} |
| **Project** | {project_name} |
| **Sent At** | {timestamp.strftime('%Y-%m-%d %H:%M:%S')} |

---

# Message Body

{full_message}

---

## Original Message

{message}

---

## Metadata

| Field | Value |
|-------|-------|
| Task Type | WhatsApp Outbound |
| Automation | Silver AI Employee |
| Status | Sent Successfully |
| Tracking | Enabled |
| Platform | WhatsApp Web |

---

## Lifecycle History

| Timestamp | From | To | Action |
|-----------|------|-----|--------|
| {timestamp.strftime('%Y-%m-%dT%H:%M:%S')} | - | Inbox | WhatsApp sent, task created |

---

## Completion

- [x] WhatsApp message sent
- [x] Task logged
- [ ] Task processed
- [ ] Task completed

Completed: [ ]
Completion Date: 
"""
    
    # Save to Inbox
    filename = f"{task_id}_whatsapp_sent.md"
    file_path = INBOX_DIR / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(task_content)
    
    return task_content


def update_task_status(task_id, status):
    """Update task file with sending status."""
    # Find the task file
    task_files = list(INBOX_DIR.glob(f"{task_id}_*.md"))
    
    if not task_files:
        return
    
    task_file = task_files[0]
    
    # Read current content
    with open(task_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add status update to lifecycle history
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    update_line = f"| {timestamp} | Inbox | Inbox | Status: {status} |\n"
    
    # Insert before the closing table marker
    if "|-----------|------|-----|--------|" in content:
        parts = content.split("|-----------|------|-----|--------|")
        if len(parts) > 1:
            content = parts[0] + "|-----------|------|-----|--------|\n" + update_line + parts[1]
    
    # Write back
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write(content)


def log_whatsapp_sent(task_id, to_number, message):
    """Log WhatsApp sent to execution log."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] WHATSAPP_SENT | Task: {task_id} | To: {to_number} | Message: {message[:50]}... | Status: Success\n"
    
    log_file = LOGS_DIR / "whatsapp_log.md"
    
    # Add header if file doesn't exist
    if not log_file.exists():
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("# WhatsApp Log\n\n")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)


def log_whatsapp_error(task_id, to_number, error):
    """Log WhatsApp error to error log."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] WHATSAPP_FAILED | Task: {task_id} | To: {to_number} | Error: {error}\n"
    
    error_log = LOGS_DIR / "error_log.md"
    
    if not error_log.exists():
        with open(error_log, 'w', encoding='utf-8') as f:
            f.write("# Error Log\n\n")
    
    with open(error_log, 'a', encoding='utf-8') as f:
        f.write(log_entry)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("="*60)
        print("📱 WHATSAPP AUTO - Send with Task Tracking")
        print("="*60)
        print()
        print("Usage: python whatsapp_auto.py <to_number> <message> [project_name]")
        print()
        print("Examples:")
        print('  python whatsapp_auto.py +923222208301 "Hello" "My Project"')
        print('  python whatsapp_auto.py +919876543210 "Meeting at 2 PM"')
        print()
        print("This will:")
        print("  1. Send the WhatsApp message")
        print("  2. Create task in Inbox/")
        print("  3. Task flows: Inbox → Needs_Action → Done")
        print("  4. Dashboard updates automatically")
        print()
        sys.exit(1)
    
    to_number = sys.argv[1]
    message = sys.argv[2]
    project_name = sys.argv[3] if len(sys.argv) > 3 else "AI Employee"
    
    success, task_id = send_whatsapp_auto(to_number, message, project_name)
    
    print()
    print("="*60)
    if success:
        print("✅ COMPLETE: WhatsApp sent + Task created + Dashboard will update")
        print()
        print("Next steps (automatic):")
        print("  1. File watcher moves task to Needs_Action/")
        print("  2. Orchestrator processes the task")
        print("  3. Task moves to Done/")
        print("  4. Dashboard updates with new metrics")
    else:
        print("❌ FAILED: Check error message above")
        print()
        print("Troubleshooting:")
        print("  - Make sure you're logged into WhatsApp Web")
        print("  - Check that the number format is correct (+92...)")
        print("  - Ensure browser is accessible")
    print("="*60)
