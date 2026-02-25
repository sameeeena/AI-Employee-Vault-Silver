"""
Simple Silver Orchestrator - FIXED Version

Processes tasks from Needs_Action → Done
Robust error handling and logging
"""

import os
import sys
import time
import json
import shutil
from pathlib import Path
from datetime import datetime
from threading import Lock
import logging
from typing import Dict, Set

# Configuration
BASE_DIR = Path(__file__).parent.absolute()
NEEDS_ACTION_DIR = BASE_DIR / "Needs_Action"
DONE_DIR = BASE_DIR / "Done"
STATE_DIR = BASE_DIR / "state"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
for dir_path in [NEEDS_ACTION_DIR, DONE_DIR, STATE_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Setup logging
log_file = LOGS_DIR / "orchestration_log.md"

# Create handlers
file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.stream.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[file_handler, stream_handler]
)
logger = logging.getLogger(__name__)

# State management
state_file = STATE_DIR / "processing_state.json"
processed_files = set()
failed_files = set()

def load_state():
    """Load processing state from file."""
    global processed_files, failed_files
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
                processed_files = set(state.get("processed_files", []))
                failed_files = set(state.get("failed_files", []))
                logger.info(f"Loaded state: {len(processed_files)} processed, {len(failed_files)} failed")
        except Exception as e:
            logger.warning(f"Could not load state: {e}")

def save_state():
    """Save processing state to file."""
    try:
        with open(state_file, 'w') as f:
            json.dump({
                "processed_files": list(processed_files),
                "failed_files": list(failed_files)
            }, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save state: {e}")

def process_task(file_path: Path) -> Dict:
    """
    Process a task file - simple classification.
    Returns processing result.
    """
    try:
        # Read task content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple classification based on content
        content_lower = content.lower()
        
        if 'email' in content_lower:
            category = 'communication'
            subcategory = 'email'
        elif 'whatsapp' in content_lower:
            category = 'communication'
            subcategory = 'whatsapp'
        elif 'bug' in content_lower or 'error' in content_lower:
            category = 'technical'
            subcategory = 'support'
        else:
            category = 'general'
            subcategory = 'misc'
        
        return {
            "success": True,
            "category": category,
            "subcategory": subcategory,
            "priority": "normal"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def move_to_done(file_path: Path):
    """Move processed file to Done directory."""
    try:
        filename = file_path.name
        dest_path = DONE_DIR / filename
        
        # Handle duplicates
        counter = 1
        stem = dest_path.stem
        suffix = dest_path.suffix
        
        while dest_path.exists():
            new_name = f"{stem}_{counter}{suffix}"
            dest_path = DONE_DIR / new_name
            counter += 1
        
        shutil.move(str(file_path), str(dest_path))
        logger.info(f"✅ Moved to Done: {dest_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Could not move to Done: {e}")
        return False

def process_all_files():
    """Process all files in Needs_Action directory."""
    files_to_process = list(NEEDS_ACTION_DIR.glob("*"))
    
    if not files_to_process:
        return
    
    logger.info(f"📂 Found {len(files_to_process)} files to process")
    
    for file_path in files_to_process:
        if not file_path.is_file():
            continue
        
        file_str = str(file_path)
        
        # Skip if already processed
        if file_str in processed_files:
            logger.info(f"⏭️  Already processed: {file_path.name}")
            continue
        
        # Skip if previously failed
        if file_str in failed_files:
            logger.warning(f"⏭️  Previously failed: {file_path.name}")
            continue
        
        # Process the file
        logger.info(f"⚙️  Processing: {file_path.name}")
        
        try:
            result = process_task(file_path)
            
            if result.get("success", False):
                # Move to Done
                if move_to_done(file_path):
                    processed_files.add(file_str)
                    save_state()
                    logger.info(f"✅ SUCCESS | Category: {result.get('category')}, Priority: {result.get('priority')}")
                else:
                    failed_files.add(file_str)
                    save_state()
                    logger.error(f"❌ FAILED | Could not move to Done")
            else:
                failed_files.add(file_str)
                save_state()
                logger.error(f"❌ FAILED | {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            failed_files.add(file_str)
            save_state()
            logger.error(f"❌ FAILED | Exception: {e}")

def main():
    """Main orchestrator loop."""
    logger.info("="*60)
    logger.info("🤖 SIMPLE SILVER ORCHESTRATOR STARTED")
    logger.info("="*60)
    logger.info(f"📂 Monitoring: {NEEDS_ACTION_DIR}")
    logger.info(f"⏱️  Processing interval: 10s")
    logger.info(f"💾 State file: {state_file}")
    logger.info("Press Ctrl+C to stop")
    logger.info("="*60)
    
    # Load existing state
    load_state()
    
    processing_interval = 10  # seconds
    
    try:
        while True:
            # Process all files
            process_all_files()
            
            # Print status
            pending = len(list(NEEDS_ACTION_DIR.glob("*")))
            done = len(list(DONE_DIR.glob("*")))
            
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Processed: {len(processed_files)} | "
                  f"Failed: {len(failed_files)} | "
                  f"Pending: {pending} | "
                  f"Done: {done}  ", 
                  end="", flush=True)
            
            # Wait for next cycle
            time.sleep(processing_interval)
            
    except KeyboardInterrupt:
        logger.info("\n\n👋 Orchestrator stopped by user")
    except Exception as e:
        logger.error(f"💥 Orchestrator error: {e}")

if __name__ == "__main__":
    main()
