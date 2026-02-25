"""
Email Sender with Guaranteed Task Creation
Creates task file FIRST, then sends email
"""

import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

load_dotenv()

# Configuration
FROM_EMAIL = os.getenv("SMTP_USERNAME", "")
PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Project paths
BASE_DIR = Path(__file__).parent.absolute()
INBOX_DIR = BASE_DIR / "Inbox"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
INBOX_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def send_email_with_tracking(to_email, subject, message, from_email=None):
    """
    Send email and create task file for tracking.
    Creates task file FIRST to ensure it's always tracked.
    """
    if not from_email:
        from_email = FROM_EMAIL

    timestamp = datetime.now()
    task_id = f"TSK-{timestamp.strftime('%Y%m%d')}-{timestamp.strftime('%H%M%S')}"
    
    print("="*60)
    print("EMAIL WITH TASK TRACKING")
    print("="*60)
    
    # STEP 1: Create task file FIRST (guaranteed)
    print(f"\n[STEP 1] Creating task file in Inbox/...")
    try:
        task_content = create_task_file(to_email, subject, message, task_id, timestamp)
        task_file = INBOX_DIR / f"{task_id}_email_sent.md"
        print(f"      SUCCESS: Task file created: {task_file.name}")
        print(f"      Location: Inbox/")
    except Exception as e:
        print(f"      FAILED: Could not create task file: {e}")
        return False, None
    
    # STEP 2: Send the email
    print(f"\n[STEP 2] Sending email to {to_email}...")
    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(from_email, PASSWORD)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        
        print(f"      SUCCESS: Email sent!")
        
        # STEP 3: Log the action
        print(f"\n[STEP 3] Logging action...")
        log_email_sent(task_id, to_email, subject)
        print(f"      Logged to email_log.md")
        
        # STEP 4: Show next steps
        print(f"\n[STEP 4] Automatic processing (wait...):")
        print(f"      File watcher will detect in ~30 seconds")
        print(f"      Moves: Inbox/ -> Needs_Action/ -> Done/")
        print(f"      Dashboard updates automatically")
        
        print()
        print("="*60)
        print("COMPLETE!")
        print("="*60)
        print(f"Task ID: {task_id}")
        print(f"Email: Sent to {to_email}")
        print(f"File: Created in Inbox/")
        print(f"Next: Automatic processing to Done/")
        
        return True, task_id
        
    except smtplib.SMTPAuthenticationError:
        print(f"      FAILED: Authentication error!")
        print(f"         Check Gmail App Password in .env")
        print(f"         Get from: https://myaccount.google.com/apppasswords")
        return False, None
        
    except Exception as e:
        print(f"      FAILED: Error: {e}")
        return False, None


def create_task_file(to_email, subject, message, task_id, timestamp):
    """Create a task file in Inbox directory."""
    
    task_content = f"""---
task_id: {task_id}
source: email
sender: {FROM_EMAIL}
recipient: {to_email}
timestamp: {timestamp.isoformat()}
received_at: {timestamp.isoformat()}
subject: {subject}
status: Inbox
priority: normal
tags: [email, sent, automated]
---

# Email Sent

## Details

| Field | Value |
|-------|-------|
| **To** | {to_email} |
| **From** | {FROM_EMAIL} |
| **Subject** | {subject} |
| **Sent At** | {timestamp.strftime('%Y-%m-%d %H:%M:%S')} |

---

# Message Body

{message}

---

## Metadata

| Field | Value |
|-------|-------|
| Task Type | Email Outbound |
| Automation | Silver AI Employee |
| Status | Sent Successfully |
| Tracking | Enabled |

---

## Lifecycle History

| Timestamp | From | To | Action |
|-----------|------|-----|--------|
| {timestamp.strftime('%Y-%m-%dT%H:%M:%S')} | - | Inbox | Email sent, task created |

---

## Completion

- [x] Email sent
- [x] Task created
- [ ] Task processed (automatic)
- [ ] Task completed (automatic)

Completed: [ ]
Completion Date: 
"""
    
    # Save to Inbox
    filename = f"{task_id}_email_sent.md"
    file_path = INBOX_DIR / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(task_content)
    
    return task_content


def log_email_sent(task_id, to_email, subject):
    """Log email sent to execution log."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] EMAIL_SENT | Task: {task_id} | To: {to_email} | Subject: {subject} | Status: Success\n"
    
    log_file = LOGS_DIR / "email_log.md"
    
    # Add header if file doesn't exist
    if not log_file.exists():
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("# Email Log\n\n")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python email_send.py <to_email> <subject> <message>")
        print()
        print("Example:")
        print('  python email_send.py john@example.com "Hello" "Test message"')
        sys.exit(1)
    
    to_email = sys.argv[1]
    subject = sys.argv[2]
    message = " ".join(sys.argv[3:])
    
    success, task_id = send_email_with_tracking(to_email, subject, message)
    
    if not success:
        sys.exit(1)
