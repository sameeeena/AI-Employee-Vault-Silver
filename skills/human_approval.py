"""
Human Approval Workflow Skill - Executable Implementation

Manages human-in-the-loop approval for sensitive actions.
"""

import json
from typing import Dict, List, Optional
from pathlib import Path
import sys
from datetime import datetime
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from skills import BaseSkill, SkillContext, SkillResult, SkillStatus, skill_registry


class HumanApprovalSkill(BaseSkill):
    """Skill for managing human-in-the-loop approval workflows."""

    APPROVAL_STATUSES = {
        "PENDING": "pending",
        "APPROVED": "approved",
        "REJECTED": "rejected",
        "ESCALATED": "escalated",
        "EXPIRED": "expired"
    }

    def __init__(self, approval_dir: Optional[str] = None):
        super().__init__(
            name="human_approval",
            description="Manages human-in-the-loop approval for sensitive actions"
        )
        self.approval_dir = Path(approval_dir) if approval_dir else None

    def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """
        Execute approval workflow.

        Args:
            context: Execution context
            **kwargs: Additional parameters (action, approval_type, metadata)

        Returns:
            SkillResult with approval outcome
        """
        try:
            approval_dir = kwargs.get("approval_dir") or self.approval_dir
            if not approval_dir:
                approval_dir = context.working_directory / "Pending_Approval"
            else:
                approval_dir = Path(approval_dir)

            action = kwargs.get("action", "request")

            if action == "request":
                result_data = self._request_approval(context, approval_dir, **kwargs)
            elif action == "check":
                result_data = self._check_approval_status(context, approval_dir, **kwargs)
            elif action == "list":
                result_data = self._list_pending_approvals(approval_dir)
            elif action == "respond":
                result_data = self._process_approval_response(context, approval_dir, **kwargs)
            else:
                return SkillResult(
                    status=SkillStatus.FAILED,
                    error_message=f"Unknown approval action: {action}"
                )

            self.logger.info(f"Approval workflow executed: {action}")

            return SkillResult(
                status=SkillStatus.SUCCESS,
                data=result_data,
                metadata={"skill": self.name, "task_id": context.task_id}
            )

        except Exception as e:
            self.logger.error(f"Approval workflow failed: {str(e)}")
            return SkillResult(
                status=SkillStatus.FAILED,
                error_message=str(e),
                metadata={"skill": self.name, "task_id": context.task_id}
            )

    def _request_approval(self, context: SkillContext, approval_dir: Path, **kwargs) -> Dict:
        """Request human approval for an action."""
        approval_dir.mkdir(parents=True, exist_ok=True)

        # Generate approval request ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        approval_id = f"APR-{timestamp}-{context.task_id[-6:] if context.task_id else '000'}"

        # Build approval request
        approval_request = {
            "approval_id": approval_id,
            "task_id": context.task_id,
            "status": self.APPROVAL_STATUSES["PENDING"],
            "requested_at": datetime.now().isoformat(),
            "expires_at": self._calculate_expiry(kwargs.get("expiry_hours", 24)),
            "action_type": kwargs.get("approval_type", "general"),
            "action_description": kwargs.get("action_description", context.task_content[:500]),
            "risk_level": kwargs.get("risk_level", "medium"),
            "requires_justification": kwargs.get("requires_justification", False),
            "metadata": {
                "task_content": context.task_content,
                "task_metadata": context.task_metadata,
                "requested_by": kwargs.get("requested_by", "system"),
                "priority": context.task_metadata.get("priority", {}) if context.task_metadata else {}
            }
        }

        # Save approval request
        approval_file = approval_dir / f"{approval_id}.json"
        with open(approval_file, 'w', encoding='utf-8') as f:
            json.dump(approval_request, f, indent=2)

        # Create human-readable summary
        summary_file = approval_dir / f"{approval_id}_summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_approval_summary(approval_request))

        self.logger.info(f"Approval request created: {approval_id}")

        return {
            "approval_id": approval_id,
            "status": "pending",
            "message": f"Approval request {approval_id} created. Awaiting human review.",
            "approval_file": str(approval_file),
            "expires_at": approval_request["expires_at"]
        }

    def _check_approval_status(self, context: SkillContext, approval_dir: Path, **kwargs) -> Dict:
        """Check the status of an approval request."""
        approval_id = kwargs.get("approval_id")

        if not approval_id:
            return {"error": "approval_id is required"}

        approval_file = approval_dir / f"{approval_id}.json"

        if not approval_file.exists():
            return {"error": f"Approval request {approval_id} not found"}

        with open(approval_file, 'r') as f:
            approval_request = json.load(f)

        # Check if expired
        if approval_request["status"] == self.APPROVAL_STATUSES["PENDING"]:
            if datetime.fromisoformat(approval_request["expires_at"]) < datetime.now():
                approval_request["status"] = self.APPROVAL_STATUSES["EXPIRED"]
                with open(approval_file, 'w') as f:
                    json.dump(approval_request, f, indent=2)

        return {
            "approval_id": approval_id,
            "status": approval_request["status"],
            "requested_at": approval_request["requested_at"],
            "expires_at": approval_request["expires_at"],
            "responded_at": approval_request.get("responded_at"),
            "response": approval_request.get("response")
        }

    def _list_pending_approvals(self, approval_dir: Path) -> Dict:
        """List all pending approval requests."""
        if not approval_dir.exists():
            return {"pending_approvals": [], "count": 0}

        pending = []
        for approval_file in approval_dir.glob("APR-*.json"):
            with open(approval_file, 'r') as f:
                approval = json.load(f)

            if approval["status"] == self.APPROVAL_STATUSES["PENDING"]:
                pending.append({
                    "approval_id": approval["approval_id"],
                    "task_id": approval.get("task_id"),
                    "action_type": approval.get("action_type"),
                    "risk_level": approval.get("risk_level"),
                    "requested_at": approval.get("requested_at"),
                    "expires_at": approval.get("expires_at")
                })

        # Sort by requested time (oldest first)
        pending.sort(key=lambda x: x.get("requested_at", ""))

        return {
            "pending_approvals": pending,
            "count": len(pending)
        }

    def _process_approval_response(self, context: SkillContext, approval_dir: Path, **kwargs) -> Dict:
        """Process a human's approval response."""
        approval_id = kwargs.get("approval_id")
        decision = kwargs.get("decision", "").lower()

        if not approval_id:
            return {"error": "approval_id is required"}

        approval_file = approval_dir / f"{approval_id}.json"

        if not approval_file.exists():
            return {"error": f"Approval request {approval_id} not found"}

        with open(approval_file, 'r') as f:
            approval_request = json.load(f)

        # Validate decision
        if decision not in ["approve", "approved", "yes", "reject", "rejected", "no", "escalate"]:
            return {"error": f"Invalid decision: {decision}"}

        # Update approval request
        now = datetime.now().isoformat()
        approval_request["status"] = (
            self.APPROVAL_STATUSES["APPROVED"] if decision in ["approve", "approved", "yes"]
            else self.APPROVAL_STATUSES["REJECTED"] if decision in ["reject", "rejected", "no"]
            else self.APPROVAL_STATUSES["ESCALATED"]
        )
        approval_request["responded_at"] = now
        approval_request["response"] = {
            "decision": decision,
            "responded_at": now,
            "responder": kwargs.get("responder", "human"),
            "justification": kwargs.get("justification", "")
        }

        # Save updated approval
        with open(approval_file, 'w') as f:
            json.dump(approval_request, f, indent=2)

        # Determine next action
        next_action = (
            "proceed_with_action" if approval_request["status"] == self.APPROVAL_STATUSES["APPROVED"]
            else "abort_action" if approval_request["status"] == self.APPROVAL_STATUSES["REJECTED"]
            else "escalate_to_higher_authority"
        )

        self.logger.info(f"Approval response processed: {approval_id} -> {approval_request['status']}")

        return {
            "approval_id": approval_id,
            "status": approval_request["status"],
            "decision": decision,
            "next_action": next_action,
            "message": f"Approval {approval_id} {approval_request['status']}"
        }

    def _calculate_expiry(self, hours: int) -> str:
        """Calculate expiry timestamp."""
        from datetime import timedelta
        expiry = datetime.now() + timedelta(hours=hours)
        return expiry.isoformat()

    def _generate_approval_summary(self, approval_request: Dict) -> str:
        """Generate a human-readable approval summary."""
        risk_emoji = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🟠",
            "critical": "🔴"
        }

        return f"""# Approval Request: {approval_request['approval_id']}

## Status: ⏳ PENDING

| Field | Value |
|-------|-------|
| **Task ID** | {approval_request.get('task_id', 'N/A')} |
| **Risk Level** | {risk_emoji.get(approval_request.get('risk_level', 'medium'), '🟡')} {approval_request.get('risk_level', 'medium').upper()} |
| **Requested At** | {approval_request.get('requested_at', 'N/A')} |
| **Expires At** | {approval_request.get('expires_at', 'N/A')} |
| **Action Type** | {approval_request.get('action_type', 'general')} |

---

## Action Description

{approval_request.get('action_description', 'No description provided')}

---

## Instructions for Reviewer

1. Review the action description above carefully
2. Assess the risk level and potential impact
3. Respond with one of the following commands:
   - `approve` - To allow the action to proceed
   - `reject` - To block the action
   - `escalate` - To forward to higher authority

**Response Location:** Update the `{approval_request['approval_id']}.json` file with your decision.

---

*Generated by Human Approval Workflow*
"""

    def get_schema(self) -> Dict:
        """Return the skill's input schema."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["request", "check", "list", "respond"],
                        "description": "The approval action to perform"
                    },
                    "approval_id": {
                        "type": "string",
                        "description": "Approval request ID (for check/respond actions)"
                    },
                    "decision": {
                        "type": "string",
                        "enum": ["approve", "reject", "escalate"],
                        "description": "Approval decision (for respond action)"
                    },
                    "approval_type": {
                        "type": "string",
                        "description": "Type of action requiring approval"
                    },
                    "action_description": {
                        "type": "string",
                        "description": "Description of the action requiring approval"
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "default": "medium"
                    },
                    "justification": {
                        "type": "string",
                        "description": "Justification for the decision"
                    }
                },
                "required": ["action"]
            }
        }


# Register the skill
skill_registry.register(HumanApprovalSkill())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Human approval workflow")
    parser.add_argument("--action", choices=["request", "check", "list", "respond"], required=True)
    parser.add_argument("--approval-id", type=str, help="Approval request ID")
    parser.add_argument("--decision", type=str, help="Approval decision")
    parser.add_argument("--description", type=str, help="Action description")
    parser.add_argument("--risk-level", type=str, default="medium")
    parser.add_argument("--approval-dir", type=str, help="Approval directory path")

    args = parser.parse_args()

    skill = HumanApprovalSkill()
    context = SkillContext(
        task_id="standalone",
        task_content=args.description or "Approval request",
        task_metadata={},
        working_directory=Path.cwd(),
        state_directory=Path.cwd() / "state",
        available_tools=[]
    )

    kwargs = {
        "action": args.action,
        "risk_level": args.risk_level,
    }
    if args.approval_id:
        kwargs["approval_id"] = args.approval_id
    if args.decision:
        kwargs["decision"] = args.decision
    if args.description:
        kwargs["action_description"] = args.description
    if args.approval_dir:
        kwargs["approval_dir"] = args.approval_dir

    result = skill.execute(context, **kwargs)
    print(json.dumps(result.to_dict(), indent=2))
