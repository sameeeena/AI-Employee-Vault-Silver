"""
Prioritize Task Skill - Executable Implementation

Determines task priority based on urgency, importance, effort, and dependencies.
"""

import json
from typing import Dict, List, Optional
from pathlib import Path
import sys
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from skills import BaseSkill, SkillContext, SkillResult, SkillStatus, skill_registry


class PrioritizeTaskSkill(BaseSkill):
    """Skill for prioritizing tasks using Eisenhower Matrix and weighted scoring."""

    # Priority factors and weights
    WEIGHTS = {
        "urgency": 0.30,
        "importance": 0.35,
        "effort": 0.15,
        "dependencies": 0.20
    }

    # Scoring rubrics
    URGENCY_SCORES = {
        "critical": 1.0,    # Must be done within 24 hours
        "high": 0.75,       # Must be done within 3 days
        "medium": 0.5,      # Should be done within a week
        "low": 0.25         # Can be done when time permits
    }

    IMPORTANCE_SCORES = {
        "critical": 1.0,    # Directly impacts revenue, compliance, or critical systems
        "high": 0.75,       // Important for goals or customer satisfaction
        "medium": 0.5,      // Nice to have, improves efficiency
        "low": 0.25         // Minimal impact if not done
    }

    EFFORT_SCORES = {
        "minimal": 1.0,     // < 30 minutes - quick wins get priority
        "low": 0.75,        // 30 min - 2 hours
        "medium": 0.5,      // 2-8 hours
        "high": 0.25        // > 8 hours - may need scheduling
    }

    def __init__(self):
        super().__init__(
            name="prioritize_task",
            description="Determines task priority using weighted scoring and Eisenhower Matrix"
        )

    def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """
        Execute task prioritization.

        Args:
            context: Execution context containing task_content, task_metadata, and classification
            **kwargs: Additional parameters (override_weights, deadline)

        Returns:
            SkillResult with priority data
        """
        try:
            metadata = context.task_metadata or {}
            classification = metadata.get("classification", {})

            # Extract or infer priority factors
            urgency = self._extract_urgency(context.task_content, classification, metadata)
            importance = self._extract_importance(context.task_content, metadata)
            effort = self._extract_effort(context.task_content, classification)
            dependencies = self._extract_dependencies(context.task_content, metadata)

            # Calculate weighted priority score
            priority_score = self._calculate_priority_score(urgency, importance, effort, dependencies)

            # Determine priority level
            priority_level = self._get_priority_level(priority_score)

            # Determine Eisenhower quadrant
            eisenhower_quadrant = self._get_eisenhower_quadrant(urgency, importance)

            # Calculate recommended action
            recommended_action = self._get_recommended_action(priority_level, eisenhower_quadrant)

            # Estimate start time
            recommended_start = self._calculate_recommended_start(priority_level, metadata)

            # Check for human review
            human_review = priority_score < 0.3 or self._has_conflicting_signals(urgency, importance, effort)

            result_data = {
                "priority_score": round(priority_score, 3),
                "priority_level": priority_level,
                "eisenhower_quadrant": eisenhower_quadrant,
                "urgency_score": self.URGENCY_SCORES.get(urgency, 0.5),
                "importance_score": self.IMPORTANCE_SCORES.get(importance, 0.5),
                "effort_score": self.EFFORT_SCORES.get(effort, 0.5),
                "dependency_score": dependencies,
                "recommended_action": recommended_action,
                "recommended_start": recommended_start.isoformat() if recommended_start else None,
                "human_review": human_review,
                "reasoning": self._generate_reasoning(priority_level, eisenhower_quadrant, urgency, importance, effort)
            }

            self.logger.info(f"Prioritized task '{context.task_id}' as '{priority_level}' (score: {priority_score:.3f})")

            return SkillResult(
                status=SkillStatus.SUCCESS,
                data=result_data,
                requires_human_approval=human_review,
                metadata={"skill": self.name, "task_id": context.task_id}
            )

        except Exception as e:
            self.logger.error(f"Prioritization failed: {str(e)}")
            return SkillResult(
                status=SkillStatus.FAILED,
                error_message=str(e),
                metadata={"skill": self.name, "task_id": context.task_id}
            )

    def _extract_urgency(self, content: str, classification: Dict, metadata: Dict) -> str:
        """Extract urgency level from task."""
        # Check explicit urgency in metadata
        if "urgency" in metadata:
            return metadata["urgency"]

        # Check classification
        if classification.get("urgency"):
            return classification["urgency"]

        # Infer from content
        content_lower = content.lower()
        if any(word in content_lower for word in ["asap", "urgent", "emergency", "critical", "immediately"]):
            return "critical"
        elif any(word in content_lower for word in ["today", "soon", "deadline", "priority"]):
            return "high"
        elif any(word in content_lower for word in ["this week", "shortly"]):
            return "medium"
        return "low"

    def _extract_importance(self, content: str, metadata: Dict) -> str:
        """Extract importance level from task."""
        if "importance" in metadata:
            return metadata["importance"]

        content_lower = content.lower()
        importance_indicators = {
            "critical": ["revenue", "compliance", "legal", "security", "critical system", "outage", "client escalation"],
            "high": ["customer", "goal", "objective", "kpi", "target", "strategic", "key"],
            "medium": ["improve", "optimize", "enhance", "efficiency", "better"],
            "low": ["nice to have", "optional", "when possible", "someday"]
        }

        for level, indicators in importance_indicators.items():
            if any(indicator in content_lower for indicator in indicators):
                return level
        return "medium"

    def _extract_effort(self, content: str, classification: Dict) -> str:
        """Extract effort level from task."""
        if "effort" in classification.get("metadata", {}):
            return classification["metadata"]["effort"]

        # Use classification complexity as proxy
        complexity = classification.get("estimated_complexity", "medium").lower()
        complexity_to_effort = {
            "low": "minimal",
            "medium": "medium",
            "high": "high"
        }
        return complexity_to_effort.get(complexity, "medium")

    def _extract_dependencies(self, content: str, metadata: Dict) -> float:
        """Extract dependency score (0-1, higher = more blocked)."""
        if "dependencies" in metadata:
            deps = metadata["dependencies"]
            if isinstance(deps, list):
                return min(len(deps) * 0.2, 1.0)
            return 0.5 if deps else 0.0

        content_lower = content.lower()
        dependency_indicators = ["waiting for", "depends on", "blocked by", "after", "once", "when complete"]
        if any(indicator in content_lower for indicator in dependency_indicators):
            return 0.7
        return 0.2

    def _calculate_priority_score(self, urgency: str, importance: str, effort: str, dependencies: float) -> float:
        """Calculate weighted priority score."""
        urgency_score = self.URGENCY_SCORES.get(urgency, 0.5)
        importance_score = self.IMPORTANCE_SCORES.get(importance, 0.5)
        effort_score = self.EFFORT_SCORES.get(effort, 0.5)

        # Dependencies reduce priority (blocked tasks can't be started)
        dependency_factor = 1.0 - (dependencies * 0.3)

        score = (
            urgency_score * self.WEIGHTS["urgency"] +
            importance_score * self.WEIGHTS["importance"] +
            effort_score * self.WEIGHTS["effort"]
        ) * dependency_factor

        return min(max(score, 0.0), 1.0)

    def _get_priority_level(self, score: float) -> str:
        """Convert score to priority level."""
        if score >= 0.8:
            return "P0_CRITICAL"
        elif score >= 0.6:
            return "P1_HIGH"
        elif score >= 0.4:
            return "P2_MEDIUM"
        elif score >= 0.2:
            return "P3_LOW"
        return "P4_BACKLOG"

    def _get_eisenhower_quadrant(self, urgency: str, importance: str) -> Dict:
        """Determine Eisenhower Matrix quadrant."""
        urgency_map = {"critical": True, "high": True, "medium": False, "low": False}
        importance_map = {"critical": True, "high": True, "medium": False, "low": False}

        is_urgent = urgency_map.get(urgency, False)
        is_important = importance_map.get(importance, False)

        if is_urgent and is_important:
            quadrant = 1
            action = "DO NOW"
        elif is_important and not is_urgent:
            quadrant = 2
            action = "SCHEDULE"
        elif is_urgent and not is_important:
            quadrant = 3
            action = "DELEGATE"
        else:
            quadrant = 4
            action = "ELIMINATE"

        return {
            "quadrant": quadrant,
            "is_urgent": is_urgent,
            "is_important": is_important,
            "action": action
        }

    def _get_recommended_action(self, priority_level: str, quadrant: Dict) -> str:
        """Get recommended action based on priority and quadrant."""
        actions = {
            "P0_CRITICAL": "Execute immediately - drop other tasks",
            "P1_HIGH": "Schedule for today/tomorrow",
            "P2_MEDIUM": "Add to this week's sprint",
            "P3_LOW": "Add to backlog, handle when capacity allows",
            "P4_BACKLOG": "Consider eliminating or automating"
        }
        return actions.get(priority_level, quadrant.get("action", "Review manually"))

    def _calculate_recommended_start(self, priority_level: str, metadata: Dict) -> Optional[datetime]:
        """Calculate recommended start time."""
        now = datetime.now()

        if priority_level == "P0_CRITICAL":
            return now
        elif priority_level == "P1_HIGH":
            return now + timedelta(hours=2)
        elif priority_level == "P2_MEDIUM":
            # Next business day
            return now + timedelta(days=1)
        elif priority_level == "P3_LOW":
            return now + timedelta(days=3)
        return None

    def _has_conflicting_signals(self, urgency: str, importance: str, effort: str) -> bool:
        """Check if there are conflicting priority signals."""
        # High urgency but low importance = conflict
        if urgency in ["critical", "high"] and importance == "low":
            return True
        # Low urgency but high importance = conflict
        if urgency == "low" and importance in ["critical", "high"]:
            return True
        return False

    def _generate_reasoning(self, priority_level: str, quadrant: Dict, urgency: str, importance: str, effort: str) -> str:
        """Generate human-readable reasoning."""
        return (
            f"Priority {priority_level}: {quadrant['action']} (Quadrant {quadrant['quadrant']}). "
            f"Urgency: {urgency}, Importance: {importance}, Effort: {effort}. "
            f"{'Conflicting signals detected - manual review recommended.' if self._has_conflicting_signals(urgency, importance, effort) else ''}"
        )

    def get_schema(self) -> Dict:
        """Return the skill's input schema."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "task_content": {"type": "string", "description": "Task description"},
                    "task_metadata": {"type": "object", "description": "Task metadata"},
                    "classification": {"type": "object", "description": "Classification results from classify_task skill"}
                },
                "required": ["task_content"]
            }
        }


# Register the skill
skill_registry.register(PrioritizeTaskSkill())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Prioritize a task")
    parser.add_argument("content", help="Task content to prioritize")
    parser.add_argument("--metadata", type=str, help="JSON metadata (optional)")

    args = parser.parse_args()

    skill = PrioritizeTaskSkill()
    context = SkillContext(
        task_id="standalone",
        task_content=args.content,
        task_metadata=json.loads(args.metadata) if args.metadata else {},
        working_directory=Path.cwd(),
        state_directory=Path.cwd() / "state",
        available_tools=[]
    )

    result = skill.execute(context)
    print(json.dumps(result.to_dict(), indent=2))
