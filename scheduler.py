#!/usr/bin/env python3
"""
Task Scheduler for Silver AI Employee

Manages scheduled tasks using Windows Task Scheduler or cron-style scheduling.
Provides API for creating, listing, and managing scheduled tasks.
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configuration
SCHEDULE_TYPES = {
    "once": "Run once at specified time",
    "daily": "Run daily at specified time",
    "weekly": "Run weekly on specified days",
    "hourly": "Run every hour",
    "interval": "Run at specified minute interval"
}


class TaskScheduler:
    """Manages scheduled tasks for the AI Employee system."""

    def __init__(self, scheduled_tasks_dir: Optional[str] = None):
        self.base_dir = Path(__file__).parent.absolute()
        self.scheduled_tasks_dir = Path(scheduled_tasks_dir) if scheduled_tasks_dir else self.base_dir / "scheduled_tasks"
        self.logs_dir = self.base_dir / "logs"
        self.state_dir = self.base_dir / "state"
        
        # Ensure directories exist
        for dir_path in [self.scheduled_tasks_dir, self.logs_dir, self.state_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Tasks file
        self.tasks_file = self.scheduled_tasks_dir / "tasks.json"
        self.tasks: Dict[str, Dict] = {}
        
        # Load existing tasks
        self._load_tasks()

    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = self.logs_dir / "scheduler_log.md"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, mode='a', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _load_tasks(self):
        """Load scheduled tasks from file."""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r') as f:
                    self.tasks = json.load(f)
                self.logger.info(f"📅 Loaded {len(self.tasks)} scheduled task(s)")
            except Exception as e:
                self.logger.warning(f"Could not load tasks: {e}")
                self.tasks = {}
        else:
            # Create default tasks
            self._create_default_tasks()

    def _create_default_tasks(self):
        """Create default scheduled tasks."""
        default_tasks = {
            "dashboard_update": {
                "id": "dashboard_update",
                "name": "Dashboard Update",
                "description": "Update dashboard metrics every 5 minutes",
                "command": "python dashboard_updater.py --action update",
                "schedule_type": "interval",
                "interval_minutes": 5,
                "enabled": True,
                "created": datetime.now().isoformat(),
                "last_run": None,
                "next_run": datetime.now().isoformat(),
                "run_count": 0
            },
            "watcher_health_check": {
                "id": "watcher_health_check",
                "name": "Watcher Health Check",
                "description": "Check watcher status every minute",
                "command": "python filesystem_watcher.py --health-check",
                "schedule_type": "interval",
                "interval_minutes": 1,
                "enabled": True,
                "created": datetime.now().isoformat(),
                "last_run": None,
                "next_run": datetime.now().isoformat(),
                "run_count": 0
            },
            "claude_reasoning": {
                "id": "claude_reasoning",
                "name": "Claude Reasoning Loop",
                "description": "Process tasks with Claude every 30 seconds",
                "command": "python claude_reasoning.py --process",
                "schedule_type": "interval",
                "interval_minutes": 0.5,
                "enabled": True,
                "created": datetime.now().isoformat(),
                "last_run": None,
                "next_run": datetime.now().isoformat(),
                "run_count": 0
            }
        }
        
        self.tasks = default_tasks
        self._save_tasks()
        self.logger.info("✅ Created default scheduled tasks")

    def _save_tasks(self):
        """Save tasks to file."""
        try:
            with open(self.tasks_file, 'w') as f:
                json.dump(self.tasks, f, indent=2)
            self.logger.info("💾 Tasks saved")
        except Exception as e:
            self.logger.error(f"Could not save tasks: {e}")

    def create_task(self, task_id: str, name: str, command: str, schedule_type: str,
                    enabled: bool = True, description: str = "", **kwargs) -> Dict:
        """Create a new scheduled task."""
        
        if schedule_type not in SCHEDULE_TYPES:
            raise ValueError(f"Invalid schedule type: {schedule_type}. Valid types: {list(SCHEDULE_TYPES.keys())}")
        
        task = {
            "id": task_id,
            "name": name,
            "description": description,
            "command": command,
            "schedule_type": schedule_type,
            "enabled": enabled,
            "created": datetime.now().isoformat(),
            "last_run": None,
            "next_run": self._calculate_next_run(schedule_type, **kwargs),
            "run_count": 0,
            "success_count": 0,
            "failure_count": 0
        }
        
        # Add schedule-specific parameters
        if schedule_type == "once":
            task["run_at"] = kwargs.get("run_at")
        elif schedule_type == "daily":
            task["run_at"] = kwargs.get("run_at", "09:00")
        elif schedule_type == "weekly":
            task["run_at"] = kwargs.get("run_at", "09:00")
            task["days"] = kwargs.get("days", ["monday"])
        elif schedule_type == "interval":
            task["interval_minutes"] = kwargs.get("interval_minutes", 5)
        
        self.tasks[task_id] = task
        self._save_tasks()
        
        self.logger.info(f"✅ Created scheduled task: {task_id}")
        return task

    def _calculate_next_run(self, schedule_type: str, **kwargs) -> str:
        """Calculate next run time based on schedule type."""
        now = datetime.now()
        
        if schedule_type == "once":
            run_at = kwargs.get("run_at")
            if run_at:
                return datetime.fromisoformat(run_at).isoformat()
            return now.isoformat()
        
        elif schedule_type == "daily":
            run_at = kwargs.get("run_at", "09:00")
            hour, minute = map(int, run_at.split(':'))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run.isoformat()
        
        elif schedule_type == "weekly":
            run_at = kwargs.get("run_at", "09:00")
            days = kwargs.get("days", ["monday"])
            hour, minute = map(int, run_at.split(':'))
            
            # Find next occurrence
            day_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                      "friday": 4, "saturday": 5, "sunday": 6}
            
            target_day = day_map.get(days[0].lower(), 0)
            days_ahead = target_day - now.weekday()
            if days_ahead < 0:
                days_ahead += 7
            
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_run += timedelta(days=days_ahead)
            return next_run.isoformat()
        
        elif schedule_type == "hourly":
            return (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0).isoformat()
        
        elif schedule_type == "interval":
            interval = kwargs.get("interval_minutes", 5)
            return (now + timedelta(minutes=interval)).isoformat()
        
        return now.isoformat()

    def delete_task(self, task_id: str) -> bool:
        """Delete a scheduled task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_tasks()
            self.logger.info(f"🗑️  Deleted task: {task_id}")
            return True
        return False

    def enable_task(self, task_id: str) -> bool:
        """Enable a scheduled task."""
        if task_id in self.tasks:
            self.tasks[task_id]["enabled"] = True
            self._save_tasks()
            self.logger.info(f"✅ Enabled task: {task_id}")
            return True
        return False

    def disable_task(self, task_id: str) -> bool:
        """Disable a scheduled task."""
        if task_id in self.tasks:
            self.tasks[task_id]["enabled"] = False
            self._save_tasks()
            self.logger.info(f"⏸️  Disabled task: {task_id}")
            return True
        return False

    def run_task(self, task_id: str) -> Dict:
        """Execute a scheduled task immediately."""
        if task_id not in self.tasks:
            return {"success": False, "error": f"Task '{task_id}' not found"}
        
        task = self.tasks[task_id]
        
        if not task["enabled"]:
            return {"success": False, "error": f"Task '{task_id}' is disabled"}
        
        try:
            self.logger.info(f"▶️  Running task: {task_id}")
            
            # Execute command
            result = subprocess.run(
                task["command"],
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(self.base_dir),
                timeout=300  # 5 minute timeout
            )
            
            # Update task stats
            task["last_run"] = datetime.now().isoformat()
            task["run_count"] = task.get("run_count", 0) + 1
            
            if result.returncode == 0:
                task["success_count"] = task.get("success_count", 0) + 1
                self.logger.info(f"✅ Task '{task_id}' completed successfully")
                return {
                    "success": True,
                    "output": result.stdout,
                    "task_id": task_id
                }
            else:
                task["failure_count"] = task.get("failure_count", 0) + 1
                self.logger.error(f"❌ Task '{task_id}' failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "output": result.stdout,
                    "task_id": task_id
                }
                
        except subprocess.TimeoutExpired:
            task["failure_count"] = task.get("failure_count", 0) + 1
            self.logger.error(f"⏱️  Task '{task_id}' timed out")
            return {"success": False, "error": "Task timed out"}
        
        except Exception as e:
            task["failure_count"] = task.get("failure_count", 0) + 1
            self.logger.error(f"❌ Task '{task_id}' error: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            # Update next run time
            task["next_run"] = self._calculate_next_run(
                task["schedule_type"],
                run_at=task.get("run_at"),
                days=task.get("days"),
                interval_minutes=task.get("interval_minutes")
            )
            self._save_tasks()

    def run_due_tasks(self) -> List[Dict]:
        """Run all tasks that are due."""
        now = datetime.now()
        results = []
        
        for task_id, task in self.tasks.items():
            if not task["enabled"]:
                continue
            
            next_run = datetime.fromisoformat(task["next_run"])
            
            if next_run <= now:
                result = self.run_task(task_id)
                results.append(result)
        
        return results

    def list_tasks(self) -> List[Dict]:
        """List all scheduled tasks."""
        return list(self.tasks.values())

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a specific task by ID."""
        return self.tasks.get(task_id)

    def get_status(self) -> Dict:
        """Get scheduler status summary."""
        total = len(self.tasks)
        enabled = sum(1 for t in self.tasks.values() if t["enabled"])
        disabled = total - enabled
        
        total_runs = sum(t.get("run_count", 0) for t in self.tasks.values())
        total_success = sum(t.get("success_count", 0) for t in self.tasks.values())
        total_failures = sum(t.get("failure_count", 0) for t in self.tasks.values())
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_tasks": total,
            "enabled": enabled,
            "disabled": disabled,
            "total_runs": total_runs,
            "total_success": total_success,
            "total_failures": total_failures,
            "success_rate": (total_success / total_runs * 100) if total_runs > 0 else 0
        }

    def create_windows_task(self, task_id: str) -> bool:
        """Create a Windows Task Scheduler task."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        # Build schtasks command
        python_exe = sys.executable
        script_dir = str(self.base_dir)
        
        # Parse command
        parts = task["command"].split(maxsplit=1)
        if len(parts) == 2:
            script = os.path.join(script_dir, parts[1])
        else:
            script = os.path.join(script_dir, parts[0])
        
        # Build XML for task
        task_name = f"SilverAI_{task_id}"
        
        try:
            # Use schtasks to create the task
            cmd = [
                "schtasks", "/Create",
                "/TN", task_name,
                "/TR", f'"{python_exe}" "{script}"',
                "/SC", "MINUTE",
                "/MO", str(task.get("interval_minutes", 5)),
                "/RL", "HIGHEST",
                "/F"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"✅ Windows task created: {task_name}")
                return True
            else:
                self.logger.error(f"Failed to create Windows task: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating Windows task: {e}")
            return False

    def delete_windows_task(self, task_id: str) -> bool:
        """Delete a Windows Task Scheduler task."""
        task_name = f"SilverAI_{task_id}"
        
        try:
            cmd = ["schtasks", "/Delete", "/TN", task_name, "/F"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"✅ Windows task deleted: {task_name}")
                return True
            else:
                self.logger.error(f"Failed to delete Windows task: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting Windows task: {e}")
            return False


def run_scheduler():
    """Run the scheduler loop."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Task Scheduler")
    parser.add_argument("--interval", type=int, default=10, help="Check interval in seconds")
    
    args = parser.parse_args()
    
    scheduler = TaskScheduler()
    
    print("\n" + "="*60)
    print("📅 TASK SCHEDULER STARTED")
    print("="*60)
    status = scheduler.get_status()
    print(f"Total Tasks: {status['total_tasks']}")
    print(f"Enabled: {status['enabled']}")
    print(f"Check Interval: {args.interval}s")
    print("="*60)
    print("\nPress Ctrl+C to stop")
    
    try:
        while True:
            # Run due tasks
            results = scheduler.run_due_tasks()
            
            if results:
                for result in results:
                    status_icon = "✅" if result.get("success") else "❌"
                    print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                          f"{status_icon} {result.get('task_id', 'unknown')}",
                          end="", flush=True)
            
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\n\nScheduler stopped by user")


def cli_manage():
    """CLI for managing scheduled tasks."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Task Scheduler CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # List tasks
    list_parser = subparsers.add_parser("list", help="List all tasks")
    
    # Add task
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("id", type=str, help="Task ID")
    add_parser.add_argument("name", type=str, help="Task name")
    add_parser.add_argument("command", type=str, help="Command to run")
    add_parser.add_argument("--schedule", type=str, default="interval", 
                           choices=list(SCHEDULE_TYPES.keys()), help="Schedule type")
    add_parser.add_argument("--interval", type=int, default=5, help="Interval in minutes")
    add_parser.add_argument("--description", type=str, default="", help="Task description")
    
    # Run task
    run_parser = subparsers.add_parser("run", help="Run a task immediately")
    run_parser.add_argument("id", type=str, help="Task ID")
    
    # Delete task
    del_parser = subparsers.add_parser("delete", help="Delete a task")
    del_parser.add_argument("id", type=str, help="Task ID")
    
    # Status
    status_parser = subparsers.add_parser("status", help="Show scheduler status")
    
    args = parser.parse_args()
    
    scheduler = TaskScheduler()
    
    if args.command == "list":
        tasks = scheduler.list_tasks()
        print(json.dumps(tasks, indent=2))
    
    elif args.command == "add":
        task = scheduler.create_task(
            task_id=args.id,
            name=args.name,
            command=args.command,
            schedule_type=args.schedule,
            description=args.description,
            interval_minutes=args.interval
        )
        print(f"✅ Task created: {json.dumps(task, indent=2)}")
    
    elif args.command == "run":
        result = scheduler.run_task(args.id)
        print(json.dumps(result, indent=2))
    
    elif args.command == "delete":
        success = scheduler.delete_task(args.id)
        print(f"{'✅ Task deleted' if success else '❌ Task not found'}")
    
    elif args.command == "status":
        status = scheduler.get_status()
        print(json.dumps(status, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    import time
    
    if len(sys.argv) > 1:
        cli_manage()
    else:
        run_scheduler()
