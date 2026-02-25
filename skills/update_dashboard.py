"""
Update Dashboard Skill - Executable Implementation

Updates the project dashboard with task metrics and system status.
"""

import json
from typing import Dict, List, Optional
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from skills import BaseSkill, SkillContext, SkillResult, SkillStatus, skill_registry


class UpdateDashboardSkill(BaseSkill):
    """Skill for updating the project dashboard with metrics and status."""

    def __init__(self, dashboard_path: Optional[str] = None):
        super().__init__(
            name="update_dashboard",
            description="Updates the project dashboard with task metrics and system status"
        )
        self.dashboard_path = Path(dashboard_path) if dashboard_path else None

    def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """
        Execute dashboard update.

        Args:
            context: Execution context containing working_directory and state_directory
            **kwargs: Additional parameters (metrics, event_type, dashboard_path)

        Returns:
            SkillResult with update outcome
        """
        try:
            dashboard_path = kwargs.get("dashboard_path") or self.dashboard_path
            if not dashboard_path:
                dashboard_path = context.working_directory / "Dashboard.md"
            else:
                dashboard_path = Path(dashboard_path)

            event_type = kwargs.get("event_type", "task_completion")
            metrics = kwargs.get("metrics", {})

            # Gather current metrics
            current_metrics = self._gather_metrics(context, metrics)

            # Update dashboard file
            update_result = self._update_dashboard_file(dashboard_path, current_metrics, event_type)

            self.logger.info(f"Dashboard updated at {dashboard_path}")

            return SkillResult(
                status=SkillStatus.SUCCESS if update_result else SkillStatus.FAILED,
                data={
                    "dashboard_path": str(dashboard_path),
                    "metrics_updated": current_metrics,
                    "event_type": event_type
                },
                metadata={"skill": self.name, "task_id": context.task_id}
            )

        except Exception as e:
            self.logger.error(f"Dashboard update failed: {str(e)}")
            return SkillResult(
                status=SkillStatus.FAILED,
                error_message=str(e),
                metadata={"skill": self.name, "task_id": context.task_id}
            )

    def _gather_metrics(self, context: SkillContext, provided_metrics: Dict) -> Dict:
        """Gather current metrics from the system."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "tasks_processed": 0,
            "tasks_failed": 0,
            "tasks_pending": 0,
            "watcher_status": "unknown",
            "orchestrator_status": "unknown",
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Merge provided metrics
        metrics.update(provided_metrics)

        # Try to read state files for accurate counts
        try:
            state_dir = context.state_directory
            state_file = state_dir / "processing_state.json"

            if state_file.exists():
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    metrics["tasks_processed"] = len(state.get("processed_files", []))
                    metrics["tasks_failed"] = len(state.get("failed_files", []))
        except Exception as e:
            self.logger.warning(f"Could not read state file: {e}")

        # Count pending files in Needs_Action
        try:
            needs_action_dir = context.working_directory / "Needs_Action"
            if needs_action_dir.exists():
                pending_files = list(needs_action_dir.glob("*"))
                metrics["tasks_pending"] = len([f for f in pending_files if f.is_file()])
        except Exception as e:
            self.logger.warning(f"Could not count pending files: {e}")

        # Check watcher status
        try:
            inbox_dir = context.working_directory / "Inbox"
            if inbox_dir.exists():
                metrics["watcher_status"] = "active"
            else:
                metrics["watcher_status"] = "inactive"
        except Exception:
            metrics["watcher_status"] = "unknown"

        return metrics

    def _update_dashboard_file(self, dashboard_path: Path, metrics: Dict, event_type: str) -> bool:
        """Update the dashboard markdown file."""
        try:
            # Generate dashboard content
            content = self._generate_dashboard_content(metrics, event_type)

            # Write to file
            dashboard_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True

        except Exception as e:
            self.logger.error(f"Failed to write dashboard: {e}")
            return False

    def _generate_dashboard_content(self, metrics: Dict, event_type: str) -> str:
        """Generate dashboard markdown content."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calculate derived metrics
        total_tasks = metrics.get("tasks_processed", 0) + metrics.get("tasks_failed", 0)
        success_rate = (
            (metrics.get("tasks_processed", 0) / total_tasks * 100)
            if total_tasks > 0 else 0
        )

        content = f"""# AI Employee Vault - Dashboard

> **Last Updated:** {now} | **Event:** {event_type}

---

## 📊 System Overview

| Metric | Value |
|--------|-------|
| **Tasks Processed** | {metrics.get('tasks_processed', 'TBD')} |
| **Tasks Failed** | {metrics.get('tasks_failed', 'TBD')} |
| **Tasks Pending** | {metrics.get('tasks_pending', 'TBD')} |
| **Success Rate** | {success_rate:.1f}% |
| **Watcher Status** | {metrics.get('watcher_status', 'TBD')} |
| **Orchestrator Status** | {metrics.get('orchestrator_status', 'TBD')} |

---

## 📈 Performance Metrics

### Task Processing

- **Total Tasks Handled:** {total_tasks}
- **Successful Completions:** {metrics.get('tasks_processed', 'TBD')}
- **Failed Tasks:** {metrics.get('tasks_failed', 'TBD')}
- **Pending Tasks:** {metrics.get('tasks_pending', 'TBD')}

### System Health

| Component | Status | Last Check |
|-----------|--------|------------|
| Filesystem Watcher | {metrics.get('watcher_status', 'TBD')} | {now} |
| Orchestrator | {metrics.get('orchestrator_status', 'TBD')} | {now} |
| Claude Integration | {metrics.get('claude_status', 'TBD')} | {now} |
| Skills Engine | {metrics.get('skills_status', 'TBD')} | {now} |

---

## 📝 Recent Activity

<!-- Activity log will be populated by the orchestrator -->

| Timestamp | Event | Status | Details |
|-----------|-------|--------|---------|
| {now} | {event_type} | Recorded | Dashboard updated |

---

## 🎯 Silver Requirements Status

| # | Requirement | Status | Notes |
|---|-------------|--------|-------|
| 1 | Bronze Requirements | ✅ | Core infrastructure operational |
| 2 | Two+ Watcher Scripts | 🔄 | In Progress |
| 3 | LinkedIn Auto-Posting | 🔄 | In Progress |
| 4 | Claude Reasoning Loop | 🔄 | In Progress |
| 5 | MCP Server | 🔄 | In Progress |
| 6 | Human-in-the-Loop | 🔄 | In Progress |
| 7 | Scheduling | 🔄 | In Progress |
| 8 | Agent Skills | ✅ | Skills framework implemented |

---

## 🔧 Configuration

- **Base Directory:** `{metrics.get('base_directory', 'Auto-detected')}`
- **State Directory:** `{metrics.get('state_directory', 'Auto-detected')}`
- **Log Directory:** `{metrics.get('log_directory', 'Auto-detected')}`

---

*Dashboard auto-generated by update_dashboard skill*
"""
        return content

    def get_schema(self) -> Dict:
        """Return the skill's input schema."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "metrics": {
                        "type": "object",
                        "description": "Metrics to update on the dashboard"
                    },
                    "event_type": {
                        "type": "string",
                        "default": "task_completion",
                        "description": "Type of event triggering the update"
                    },
                    "dashboard_path": {
                        "type": "string",
                        "description": "Path to the dashboard file (optional)"
                    }
                },
                "required": []
            }
        }


# Register the skill
skill_registry.register(UpdateDashboardSkill())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Update dashboard")
    parser.add_argument("--metrics", type=str, help="JSON metrics to update")
    parser.add_argument("--event-type", default="manual_update", help="Event type")
    parser.add_argument("--dashboard-path", type=str, help="Path to dashboard file")

    args = parser.parse_args()

    skill = UpdateDashboardSkill()
    context = SkillContext(
        task_id="standalone",
        task_content="Manual dashboard update",
        task_metadata={},
        working_directory=Path.cwd(),
        state_directory=Path.cwd() / "state",
        available_tools=[]
    )

    metrics = json.loads(args.metrics) if args.metrics else {}
    result = skill.execute(
        context,
        metrics=metrics,
        event_type=args.event_type,
        dashboard_path=args.dashboard_path
    )
    print(json.dumps(result.to_dict(), indent=2))
