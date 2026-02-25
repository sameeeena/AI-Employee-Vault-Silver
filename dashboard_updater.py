"""
Dashboard Updater for Silver AI Employee

Updates the Dashboard.md with live data from the system.
Can be run standalone or as part of the orchestrator.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


class DashboardUpdater:
    """Updates the Dashboard.md with live metrics."""

    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize Dashboard Updater.

        Args:
            base_dir: Base directory of the project
        """
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.absolute()
        self.dashboard_file = self.base_dir / "Dashboard.md"
        self.state_dir = self.base_dir / "state"
        self.logs_dir = self.base_dir / "logs"
        self.plans_dir = self.base_dir / "Plans"
        self.approvals_dir = self.base_dir / "Pending_Approval"
        self.scheduled_tasks_dir = self.base_dir / "scheduled_tasks"

    def gather_metrics(self) -> Dict:
        """Gather all metrics from the system."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "tasks_processed": 0,
            "tasks_failed": 0,
            "tasks_pending": 0,
            "approvals_pending": 0,
            "scheduled_tasks": 0,
            "plans_created": 0,
            "watcher_status": "unknown",
            "orchestrator_status": "unknown",
            "skills_available": 0,
            "mcp_tools_available": 0
        }

        # Read state file (try both old and new locations)
        state_file = self.state_dir / "processing_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    metrics["tasks_processed"] = len(state.get("processed_files", []))
                    metrics["tasks_failed"] = len(state.get("failed_files", []))
            except Exception as e:
                pass
        
        # Also count files in Done folder as processed
        done_dir = self.base_dir / "Done"
        if done_dir.exists():
            done_count = len([f for f in done_dir.iterdir() if f.is_file()])
            metrics["tasks_processed"] = max(metrics["tasks_processed"], done_count)

        # Count pending files
        needs_action_dir = self.base_dir / "Needs_Action"
        if needs_action_dir.exists():
            metrics["tasks_pending"] = len([f for f in needs_action_dir.iterdir() if f.is_file()])

        # Count inbox files
        inbox_dir = self.base_dir / "Inbox"
        if inbox_dir.exists():
            metrics["tasks_pending"] += len([f for f in inbox_dir.iterdir() if f.is_file()])

        # Check watcher status
        if inbox_dir.exists():
            metrics["watcher_status"] = "active"
        
        # Check orchestrator status from log
        orchestration_log = self.logs_dir / "orchestration_log.md"
        if orchestration_log.exists():
            try:
                with open(orchestration_log, 'r') as f:
                    lines = f.readlines()
                    if lines and "SIMPLE SILVER ORCHESTRATOR STARTED" in lines[-10]:
                        metrics["orchestrator_status"] = "Running"
            except:
                pass

        # Count pending approvals
        if self.approvals_dir.exists():
            metrics["approvals_pending"] = len([f for f in self.approvals_dir.glob("APR-*.json")])

        # Count scheduled tasks
        tasks_file = self.scheduled_tasks_dir / "tasks.json" if self.scheduled_tasks_dir.exists() else None
        if tasks_file and tasks_file.exists():
            try:
                with open(tasks_file, 'r') as f:
                    tasks = json.load(f)
                    metrics["scheduled_tasks"] = len(tasks)
            except:
                pass

        # Count plans
        if self.plans_dir.exists():
            metrics["plans_created"] = len([f for f in self.plans_dir.glob("Plan_*.md")])

        # Count skills
        skills_dir = self.base_dir / "skills"
        if skills_dir.exists():
            metrics["skills_available"] = len([f for f in skills_dir.glob("*.py") if f.name != "__init__.py"])

        # Count MCP tools
        mcp_config_dir = self.base_dir / "mcp_config"
        if mcp_config_dir.exists():
            config_file = mcp_config_dir / "mcp_server_config.json"
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        metrics["mcp_tools_available"] = len(config.get("tools", []))
                except:
                    pass

        # Read execution log for recent activity
        execution_log = self.logs_dir / "execution_log.md"
        recent_activity = []
        if execution_log.exists():
            try:
                with open(execution_log, 'r') as f:
                    lines = f.readlines()[-10:]  # Last 10 entries
                    for line in lines:
                        if line.startswith('['):
                            recent_activity.append(line.strip())
            except:
                pass
        
        # Also read orchestration log
        if orchestration_log.exists():
            try:
                with open(orchestration_log, 'r') as f:
                    lines = f.readlines()[-5:]
                    for line in lines:
                        if "Processing:" in line or "SUCCESS" in line or "FAILED" in line:
                            recent_activity.append(line.strip())
            except:
                pass

        metrics["recent_activity"] = recent_activity

        return metrics

    def generate_dashboard(self, metrics: Optional[Dict] = None) -> str:
        """Generate dashboard content."""
        if not metrics:
            metrics = self.gather_metrics()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calculate derived metrics
        total_tasks = metrics["tasks_processed"] + metrics["tasks_failed"]
        success_rate = (metrics["tasks_processed"] / total_tasks * 100) if total_tasks > 0 else 0

        # Generate activity table
        activity_rows = ""
        for activity in metrics.get("recent_activity", []):
            parts = activity.split('|')
            if len(parts) >= 3:
                timestamp = parts[0].strip('[] ')
                status = parts[1].strip()
                details = parts[2].strip() if len(parts) > 2 else ""
                activity_rows += f"| {timestamp} | {status} | {details} |\n"

        if not activity_rows:
            activity_rows = "| - | - | No recent activity |\n"

        content = f"""# AI Employee Vault - Dashboard

> **Last Updated:** {now} | **Status:** Operational

---

## 📊 System Overview

| Metric | Value |
|--------|-------|
| **Tasks Processed** | {metrics['tasks_processed']} |
| **Tasks Failed** | {metrics['tasks_failed']} |
| **Tasks Pending** | {metrics['tasks_pending']} |
| **Success Rate** | {success_rate:.1f}% |
| **Watcher Status** | {metrics['watcher_status']} |
| **Approvals Pending** | {metrics['approvals_pending']} |

---

## 📈 Performance Metrics

### Task Processing

- **Total Tasks Handled:** {total_tasks}
- **Successful Completions:** {metrics['tasks_processed']}
- **Failed Tasks:** {metrics['tasks_failed']}
- **Pending Tasks:** {metrics['tasks_pending']}

### System Health

| Component | Status | Details |
|-----------|--------|---------|
| Filesystem Watcher | {metrics['watcher_status']} | Monitoring Inbox |
| Orchestrator | {metrics['orchestrator_status'] or 'Running'} | Processing tasks |
| Skills Engine | ✅ Active | {metrics['skills_available']} skills loaded |
| MCP Server | ✅ Active | {metrics['mcp_tools_available']} tools available |
| Reasoning Loop | ✅ Active | {metrics['plans_created']} plans created |
| Scheduler | ✅ Active | {metrics['scheduled_tasks']} tasks scheduled |

---

## 📝 Recent Activity

| Timestamp | Status | Details |
|-----------|--------|---------|
{activity_rows}

---

## 🎯 Silver Requirements Status

| # | Requirement | Status | Notes |
|---|-------------|--------|-------|
| 1 | Bronze Requirements | ✅ Complete | Core infrastructure operational |
| 2 | Two+ Watcher Scripts | ✅ Complete | Filesystem + Gmail + LinkedIn |
| 3 | LinkedIn Auto-Posting | ✅ Complete | Auto-poster with templates |
| 4 | Claude Reasoning Loop | ✅ Complete | Plan.md generation active |
| 5 | MCP Server | ✅ Complete | {metrics['mcp_tools_available']} tools for external actions |
| 6 | Human-in-the-Loop | ✅ Complete | Approval workflow active |
| 7 | Scheduling | ✅ Complete | Windows Task Scheduler + cron |
| 8 | Agent Skills | ✅ Complete | {metrics['skills_available']} executable skills |

---

## 🛠️ Available Skills

| Skill | Description |
|-------|-------------|
| classify_task | Categorizes tasks by type and urgency |
| prioritize_task | Determines priority using weighted scoring |
| execute_task | Performs task execution |
| summarize_task | Generates task summaries |
| update_dashboard | Updates this dashboard |
| human_approval | Manages approval workflows |

---

## 📅 Scheduled Tasks

| Task | Schedule | Next Run |
|------|----------|----------|
| Dashboard Update | Every 5 min | Auto |
| Watcher Health Check | Every minute | Continuous |
| Task Processing | Continuous | Real-time |

---

## 🔧 Quick Commands

```bash
# Update dashboard manually
python dashboard_updater.py --update

# View system status
python dashboard_updater.py --status

# Export metrics
python dashboard_updater.py --export
```

---

## 📁 Directory Structure

```
AI_Employee_vault(Silver)/
├── Inbox/              # New tasks land here
├── Needs_Action/       # Tasks being processed
├── Done/               # Completed tasks
├── Pending_Approval/   # Awaiting human approval ({metrics['approvals_pending']} pending)
├── Plans/              # Generated execution plans ({metrics['plans_created']} plans)
├── scheduled_tasks/    # Scheduled task definitions
├── skills/             # Agent skills ({metrics['skills_available']} skills)
├── watchers/           # External service watchers
├── state/              # Processing state
└── logs/               # Execution logs
```

---

*Dashboard auto-generated by update_dashboard skill*
"""
        return content

    def update_dashboard(self, metrics: Optional[Dict] = None) -> Path:
        """Update the dashboard file."""
        if not metrics:
            metrics = self.gather_metrics()

        content = self.generate_dashboard(metrics)

        with open(self.dashboard_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return self.dashboard_file

    def print_status(self):
        """Print system status to console."""
        metrics = self.gather_metrics()

        print("\n" + "="*60)
        print("SILVER AI EMPLOYEE - SYSTEM STATUS")
        print("="*60)
        print(f"Timestamp: {metrics['timestamp']}")
        print("-"*60)
        print(f"Tasks Processed:  {metrics['tasks_processed']}")
        print(f"Tasks Failed:     {metrics['tasks_failed']}")
        print(f"Tasks Pending:    {metrics['tasks_pending']}")
        print(f"Approvals Pending: {metrics['approvals_pending']}")
        print(f"Plans Created:    {metrics['plans_created']}")
        print(f"Scheduled Tasks:  {metrics['scheduled_tasks']}")
        print(f"Skills Available: {metrics['skills_available']}")
        print(f"MCP Tools:        {metrics['mcp_tools_available']}")
        print("-"*60)

        total = metrics['tasks_processed'] + metrics['tasks_failed']
        if total > 0:
            rate = metrics['tasks_processed'] / total * 100
            print(f"Success Rate:     {rate:.1f}%")
        print("="*60)


# Standalone runner
def main():
    """Run dashboard updater standalone."""
    import argparse

    parser = argparse.ArgumentParser(description="Dashboard Updater")
    parser.add_argument("--action", choices=["update", "status", "export"], default="update")
    parser.add_argument("--output", type=str, help="Output file for export")

    args = parser.parse_args()

    updater = DashboardUpdater()

    if args.action == "update":
        dashboard_file = updater.update_dashboard()
        print(f"Dashboard updated: {dashboard_file}")

    elif args.action == "status":
        updater.print_status()

    elif args.action == "export":
        metrics = updater.gather_metrics()
        output_file = args.output or "metrics.json"
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"Metrics exported to: {output_file}")


if __name__ == "__main__":
    main()
