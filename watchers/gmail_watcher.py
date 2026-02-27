#!/usr/bin/env python3
"""
Gmail Watcher for Silver AI Employee

Monitors Gmail for new emails and creates tasks in the Inbox folder.
Uses Gmail API with OAuth2 authentication.
"""

import os
import sys
import time
import base64
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set
import pickle

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'client_secret_*.json'

class GmailWatcher:
    """Watches Gmail for new emails and creates tasks."""

    def __init__(self, inbox_dir: Optional[str] = None, credentials_dir: Optional[str] = None):
        self.base_dir = Path(__file__).parent.parent.absolute()
        self.inbox_dir = Path(inbox_dir) if inbox_dir else self.base_dir / "Inbox"
        self.credentials_dir = Path(credentials_dir) if credentials_dir else self.base_dir
        self.logs_dir = self.base_dir / "logs"
        self.state_dir = self.base_dir / "state"
        
        # Ensure directories exist
        for dir_path in [self.inbox_dir, self.logs_dir, self.state_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Gmail API service
        self.service = None
        self.creds = None
        
        # State tracking
        self.seen_message_ids: Set[str] = set()
        self.last_check_time = datetime.now()
        
        # Load state
        self._load_state()

    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = self.logs_dir / "gmail_watcher_log.md"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, mode='a', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _load_state(self):
        """Load previously seen message IDs."""
        state_file = self.state_dir / "gmail_state.json"
        if state_file.exists():
            try:
                import json
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.seen_message_ids = set(state.get("seen_message_ids", []))
                    self.logger.info(f"Loaded Gmail state: {len(self.seen_message_ids)} seen messages")
            except Exception as e:
                self.logger.warning(f"Could not load Gmail state: {e}")

    def _save_state(self):
        """Save seen message IDs to state file."""
        state_file = self.state_dir / "gmail_state.json"
        try:
            import json
            # Keep only last 1000 message IDs to prevent unbounded growth
            seen_list = list(self.seen_message_ids)[-1000:]
            with open(state_file, 'w') as f:
                json.dump({"seen_message_ids": seen_list}, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save Gmail state: {e}")

    def authenticate(self) -> bool:
        """Authenticate with Gmail API."""
        try:
            # Find credentials file
            creds_files = list(self.credentials_dir.glob(CREDENTIALS_FILE))
            if not creds_files:
                self.logger.error(f"No credentials file found matching {CREDENTIALS_FILE}")
                return False
            
            creds_file = creds_files[0]
            token_path = self.credentials_dir / TOKEN_FILE
            
            # Load existing credentials
            if token_path.exists():
                with open(token_path, 'rb') as token:
                    self.creds = pickle.load(token)
            
            # Refresh or get new credentials
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(creds_file), SCOPES)
                    self.creds = flow.run_local_server(port=0)
                
                # Save credentials
                with open(token_path, 'wb') as token:
                    pickle.dump(self.creds, token)
            
            # Build service
            self.service = build('gmail', 'v1', credentials=self.creds)
            self.logger.info("✅ Gmail authentication successful")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Gmail authentication failed: {e}")
            return False

    def get_unread_emails(self, max_results: int = 10) -> List[Dict]:
        """Fetch unread emails from Gmail."""
        if not self.service:
            self.logger.error("Gmail service not initialized")
            return []
        
        try:
            # List unread messages
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return []
            
            emails = []
            for msg in messages:
                email_data = self._get_email_details(msg['id'])
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except HttpError as error:
            self.logger.error(f"Gmail API error: {error}")
            return []

    def _get_email_details(self, message_id: str) -> Optional[Dict]:
        """Get detailed email information."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract body
            body = self._extract_body(message)
            
            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'thread_id': message.get('threadId', '')
            }
            
        except Exception as e:
            self.logger.error(f"Error getting email details: {e}")
            return None

    def _extract_body(self, message: Dict) -> str:
        """Extract email body from message."""
        try:
            parts = message['payload']['parts']
            
            # Look for text/plain or text/html part
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    body_data = part['body'].get('data', '')
                    if body_data:
                        return base64.urlsafe_b64decode(body_data).decode('utf-8')
                elif part['mimeType'] == 'text/html':
                    body_data = part['body'].get('data', '')
                    if body_data:
                        # Return HTML stripped (simple approach)
                        html = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        # Simple HTML tag removal
                        import re
                        return re.sub('<.*?>', '', html)
            
            # Fallback to main body
            if 'body' in message['payload'] and message['payload']['body'].get('data'):
                body_data = message['payload']['body']['data']
                return base64.urlsafe_b64decode(body_data).decode('utf-8')
            
            return ''
            
        except Exception as e:
            self.logger.error(f"Error extracting body: {e}")
            return ''

    def mark_email_read(self, message_id: str) -> bool:
        """Mark email as read."""
        try:
            if self.service:
                self.service.users().messages().modify(
                    userId='me',
                    id=message_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
                return True
        except Exception as e:
            self.logger.error(f"Error marking email as read: {e}")
        return False

    def create_task_from_email(self, email: Dict) -> Optional[Path]:
        """Create a task file from an email."""
        try:
            # Generate task ID
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            task_id = f"TSK-{timestamp}-gmail"
            
            # Sanitize subject for filename
            safe_subject = "".join(c if c.isalnum() or c in ' -_' else '_' for c in email['subject'][:30])
            
            # Create task file content
            task_content = f"""# Task: {email['subject']}

**Task ID:** {task_id}
**Source:** gmail
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Email Details

| Field | Value |
|-------|-------|
| **From** | {email['sender']} |
| **Subject** | {email['subject']} |
| **Date** | {email['date']} |
| **Gmail ID** | {email['id']} |

---

## Email Body

{email['body']}

---

## Processing Status

- [ ] Classify task
- [ ] Prioritize task
- [ ] Execute required actions
- [ ] Mark email as read

---

*Created by Gmail Watcher*
"""
            
            # Save task file
            task_file = self.inbox_dir / f"{task_id}_gmail_{safe_subject}.md"
            with open(task_file, 'w', encoding='utf-8') as f:
                f.write(task_content)
            
            self.logger.info(f"✅ Task created from email: {task_file.name}")
            return task_file
            
        except Exception as e:
            self.logger.error(f"Error creating task from email: {e}")
            return None

    def process_new_emails(self) -> int:
        """Process new unread emails."""
        emails = self.get_unread_emails(max_results=10)
        
        if not emails:
            self.logger.info("No new unread emails")
            return 0
        
        processed_count = 0
        for email in emails:
            # Skip if already processed
            if email['id'] in self.seen_message_ids:
                continue
            
            # Create task
            task_file = self.create_task_from_email(email)
            if task_file:
                # Mark as seen and read
                self.seen_message_ids.add(email['id'])
                self.mark_email_read(email['id'])
                processed_count += 1
        
        # Save state
        self._save_state()
        
        self.logger.info(f"Processed {processed_count} new email(s)")
        return processed_count

    def run(self, check_interval: int = 60):
        """Run the Gmail watcher loop."""
        self.logger.info("="*60)
        self.logger.info("📧 GMAIL WATCHER STARTED")
        self.logger.info("="*60)
        self.logger.info(f"📂 Inbox Directory: {self.inbox_dir}")
        self.logger.info(f"⏱️  Check Interval: {check_interval}s")
        self.logger.info("Press Ctrl+C to stop")
        self.logger.info("="*60)
        
        # Authenticate
        if not self.authenticate():
            self.logger.error("Failed to authenticate. Exiting.")
            return
        
        try:
            while True:
                # Process new emails
                count = self.process_new_emails()
                
                # Print status
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                      f"Gmail: {count} new | "
                      f"Seen: {len(self.seen_message_ids)}  ",
                      end="", flush=True)
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("\n\n Gmail watcher stopped by user")
        except Exception as e:
            self.logger.error(f"💥 Gmail watcher error: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gmail Watcher")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    
    args = parser.parse_args()
    
    watcher = GmailWatcher()
    watcher.run(check_interval=args.interval)


if __name__ == "__main__":
    main()
