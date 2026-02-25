"""
Classify Task Skill - Executable Implementation

Automatically categorizes incoming tasks based on their content, urgency, and complexity.
"""

import json
import re
from typing import Dict, List, Optional
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from skills import BaseSkill, SkillContext, SkillResult, SkillStatus, skill_registry


class ClassifyTaskSkill(BaseSkill):
    """Skill for classifying tasks into categories."""

    # Category taxonomy
    CATEGORIES = {
        "technical": ["code", "programming", "api", "database", "server", "deployment", "bug", "feature"],
        "administrative": ["meeting", "schedule", "email", "document", "report", "approval", "review"],
        "creative": ["design", "write", "content", "marketing", "brand", "visual", "artwork"],
        "analytical": ["analyze", "data", "metrics", "report", "insight", "trend", "research"],
        "sales": ["lead", "prospect", "client", "proposal", "quote", "contract", "deal"],
        "support": ["customer", "issue", "ticket", "help", "question", "problem", "complaint"]
    }

    URGENCY_KEYWORDS = {
        "critical": ["urgent", "asap", "immediately", "emergency", "critical", "blocker"],
        "high": ["priority", "important", "soon", "today", "deadline"],
        "medium": ["this week", "shortly", "when possible"],
        "low": ["sometime", "whenever", "no rush", "backlog"]
    }

    COMPLEXITY_INDICATORS = {
        "high": ["complex", "multi-step", "integrate", "architecture", "redesign", "overhaul"],
        "medium": ["update", "modify", "enhance", "optimize", "refactor"],
        "low": ["fix", "add", "change", "simple", "quick", "minor"]
    }

    def __init__(self):
        super().__init__(
            name="classify_task",
            description="Automatically categorizes tasks based on content, urgency, and complexity"
        )

    def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """
        Execute task classification.

        Args:
            context: Execution context containing task_content and task_metadata
            **kwargs: Additional parameters (category_rules, use_ai)

        Returns:
            SkillResult with classification data
        """
        try:
            task_content = context.task_content.lower()
            metadata = context.task_metadata or {}

            # Classify primary category
            primary_category, category_scores = self._classify_category(task_content)

            # Assess urgency
            urgency = self._assess_urgency(task_content)

            # Determine complexity
            complexity = self._determine_complexity(task_content)

            # Estimate time
            estimated_time = self._estimate_time(complexity, urgency)

            # Calculate confidence
            confidence = self._calculate_confidence(category_scores)

            # Determine if human review needed
            requires_human_review = confidence < 0.5 or primary_category == "unknown"

            result_data = {
                "primary_category": primary_category,
                "secondary_categories": self._get_secondary_categories(category_scores, primary_category),
                "urgency": urgency,
                "confidence_score": round(confidence, 2),
                "estimated_complexity": complexity,
                "estimated_time": estimated_time,
                "requires_human_review": requires_human_review,
                "reasoning": self._generate_reasoning(primary_category, urgency, complexity, confidence),
                "category_scores": category_scores
            }

            self.logger.info(f"Classified task '{context.task_id}' as '{primary_category}' (confidence: {confidence:.2f})")

            return SkillResult(
                status=SkillStatus.SUCCESS,
                data=result_data,
                requires_human_approval=requires_human_review,
                metadata={"skill": self.name, "task_id": context.task_id}
            )

        except Exception as e:
            self.logger.error(f"Classification failed: {str(e)}")
            return SkillResult(
                status=SkillStatus.FAILED,
                error_message=str(e),
                metadata={"skill": self.name, "task_id": context.task_id}
            )

    def _classify_category(self, content: str) -> tuple[str, Dict[str, int]]:
        """Classify content into a primary category."""
        category_scores = {}

        for category, keywords in self.CATEGORIES.items():
            score = sum(1 for keyword in keywords if keyword in content)
            category_scores[category] = score

        if not category_scores or max(category_scores.values()) == 0:
            return "unknown", category_scores

        primary = max(category_scores, key=category_scores.get)
        return primary, category_scores

    def _assess_urgency(self, content: str) -> str:
        """Assess task urgency from content."""
        for urgency_level, keywords in self.URGENCY_KEYWORDS.items():
            if any(keyword in content for keyword in keywords):
                return urgency_level
        return "medium"  # Default urgency

    def _determine_complexity(self, content: str) -> str:
        """Determine task complexity from content."""
        for complexity_level, indicators in self.COMPLEXITY_INDICATORS.items():
            if any(indicator in content for indicator in indicators):
                return complexity_level

        # Default based on content length
        word_count = len(content.split())
        if word_count > 200:
            return "high"
        elif word_count > 50:
            return "medium"
        return "low"

    def _estimate_time(self, complexity: str, urgency: str) -> str:
        """Estimate time required based on complexity and urgency."""
        time_estimates = {
            ("low", "critical"): "30 minutes",
            ("low", "high"): "1 hour",
            ("low", "medium"): "2 hours",
            ("low", "low"): "4 hours",
            ("medium", "critical"): "2 hours",
            ("medium", "high"): "4 hours",
            ("medium", "medium"): "1 day",
            ("medium", "low"): "2 days",
            ("high", "critical"): "1 day",
            ("high", "high"): "3 days",
            ("high", "medium"): "5 days",
            ("high", "low"): "1 week",
        }
        return time_estimates.get((complexity, urgency), "1 day")

    def _calculate_confidence(self, category_scores: Dict[str, int]) -> float:
        """Calculate confidence score for classification."""
        if not category_scores:
            return 0.0

        total = sum(category_scores.values())
        if total == 0:
            return 0.0

        max_score = max(category_scores.values())
        second_max = sorted(category_scores.values(), reverse=True)[1] if len(category_scores) > 1 else 0

        # Base confidence on score dominance
        if max_score == 0:
            return 0.2

        dominance = (max_score - second_max) / max_score if max_score > 0 else 0
        base_confidence = min(max_score / 5, 1.0)  # Normalize to max 5 matches

        return (base_confidence * 0.6) + (dominance * 0.4)

    def _get_secondary_categories(self, category_scores: Dict[str, int], primary: str) -> List[str]:
        """Get secondary categories based on scores."""
        sorted_categories = sorted(
            [(cat, score) for cat, score in category_scores.items() if cat != primary and score > 0],
            key=lambda x: x[1],
            reverse=True
        )
        return [cat for cat, _ in sorted_categories[:2]]

    def _generate_reasoning(self, primary: str, urgency: str, complexity: str, confidence: float) -> str:
        """Generate human-readable reasoning for classification."""
        reasoning_parts = [
            f"Classified as '{primary}' category",
            f"with {urgency} urgency",
            f"and {complexity} complexity"
        ]

        if confidence < 0.5:
            reasoning_parts.append("(low confidence - may require manual review)")
        elif confidence > 0.8:
            reasoning_parts.append("(high confidence)")

        return " ".join(reasoning_parts)

    def get_schema(self) -> Dict:
        """Return the skill's input schema."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "task_content": {
                        "type": "string",
                        "description": "The raw task description or request"
                    },
                    "task_metadata": {
                        "type": "object",
                        "description": "Optional metadata including source, timestamp, priority hint"
                    },
                    "use_ai": {
                        "type": "boolean",
                        "description": "Whether to use AI for enhanced classification",
                        "default": False
                    }
                },
                "required": ["task_content"]
            }
        }


# Register the skill
skill_registry.register(ClassifyTaskSkill())


# Standalone execution support
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Classify a task")
    parser.add_argument("content", help="Task content to classify")
    parser.add_argument("--metadata", type=str, help="JSON metadata (optional)")

    args = parser.parse_args()

    skill = ClassifyTaskSkill()
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
