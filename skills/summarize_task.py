"""
Summarize Task Skill - Executable Implementation

Generates concise summaries of tasks, outcomes, and execution results.
"""

import json
import re
from typing import Dict, List, Optional
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from skills import BaseSkill, SkillContext, SkillResult, SkillStatus, skill_registry


class SummarizeTaskSkill(BaseSkill):
    """Skill for generating concise summaries of tasks and outcomes."""

    def __init__(self):
        super().__init__(
            name="summarize_task",
            description="Generates concise summaries of tasks, outcomes, and execution results"
        )

    def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """
        Execute task summarization.

        Args:
            context: Execution context containing task_content and execution results
            **kwargs: Additional parameters (summary_type, max_length, include_metadata)

        Returns:
            SkillResult with summary data
        """
        try:
            summary_type = kwargs.get("summary_type", "executive")
            max_length = kwargs.get("max_length", 500)
            include_metadata = kwargs.get("include_metadata", True)

            # Generate summary based on type
            if summary_type == "executive":
                summary = self._generate_executive_summary(context.task_content, context.task_metadata, max_length)
            elif summary_type == "technical":
                summary = self._generate_technical_summary(context.task_content, context.task_metadata, max_length)
            elif summary_type == "outcome":
                summary = self._generate_outcome_summary(context.task_content, context.task_metadata, kwargs.get("execution_result", {}), max_length)
            else:
                summary = self._generate_executive_summary(context.task_content, context.task_metadata, max_length)

            # Extract key points
            key_points = self._extract_key_points(context.task_content, 5)

            # Generate action items
            action_items = self._extract_action_items(context.task_content)

            result_data = {
                "summary": summary,
                "summary_type": summary_type,
                "key_points": key_points,
                "action_items": action_items,
                "word_count": len(summary.split()),
                "metadata": context.task_metadata if include_metadata else None
            }

            self.logger.info(f"Generated {summary_type} summary for task '{context.task_id}' ({len(summary)} chars)")

            return SkillResult(
                status=SkillStatus.SUCCESS,
                data=result_data,
                metadata={"skill": self.name, "task_id": context.task_id}
            )

        except Exception as e:
            self.logger.error(f"Summarization failed: {str(e)}")
            return SkillResult(
                status=SkillStatus.FAILED,
                error_message=str(e),
                metadata={"skill": self.name, "task_id": context.task_id}
            )

    def _generate_executive_summary(self, content: str, metadata: Dict, max_length: int) -> str:
        """Generate an executive summary focusing on business impact."""
        # Extract first meaningful sentence
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]

        if not sentences:
            return content[:max_length] if len(content) > max_length else content

        # Build summary from key sentences
        summary_parts = []
        current_length = 0

        for sentence in sentences[:5]:
            if current_length + len(sentence) > max_length:
                break
            summary_parts.append(sentence)
            current_length += len(sentence) + 1

        summary = ". ".join(summary_parts)
        if summary_parts:
            summary += "."

        return summary if summary else content[:max_length]

    def _generate_technical_summary(self, content: str, metadata: Dict, max_length: int) -> str:
        """Generate a technical summary focusing on implementation details."""
        # Extract technical terms and code references
        tech_patterns = [
            r'\b[A-Z][a-zA-Z0-9_]+\b',  # CamelCase identifiers
            r'[a-z]+_[a-z]+',  # snake_case identifiers
            r'`[^`]+`',  # Code in backticks
            r'\b(?:API|HTTP|REST|JSON|SQL|NoSQL|AWS|Azure|GCP)\b',  # Tech acronyms
        ]

        tech_terms = []
        for pattern in tech_patterns:
            tech_terms.extend(re.findall(pattern, content))

        # Get first paragraph for context
        paragraphs = content.split('\n\n')
        context = paragraphs[0] if paragraphs else content

        summary = f"Technical Context: {context[:200]}"
        if tech_terms:
            unique_terms = list(set(tech_terms))[:10]
            summary += f"\n\nKey Technical Elements: {', '.join(unique_terms)}"

        return summary[:max_length] if len(summary) > max_length else summary

    def _generate_outcome_summary(self, content: str, metadata: Dict, execution_result: Dict, max_length: int) -> str:
        """Generate a summary including execution outcomes."""
        status = execution_result.get("status", "unknown")
        result_data = execution_result.get("data", {})

        outcome_parts = [
            f"Task Status: {status}",
            f"Original Task: {content[:150]}..." if len(content) > 150 else f"Original Task: {content}"
        ]

        if execution_result.get("error_message"):
            outcome_parts.append(f"Error: {execution_result['error_message'][:200]}")

        if result_data:
            if isinstance(result_data, dict):
                for key, value in list(result_data.items())[:3]:
                    outcome_parts.append(f"{key}: {str(value)[:100]}")

        return "\n".join(outcome_parts)[:max_length]

    def _extract_key_points(self, content: str, max_points: int = 5) -> List[str]:
        """Extract key points from content."""
        # Look for bullet points, numbered lists, or key sentences
        key_points = []

        # Extract bullet points
        bullet_patterns = [
            r'[-*•]\s*(.+?)(?:\n|$)',
            r'\d+\.\s*(.+?)(?:\n|$)',
            r'^(?:Key|Important|Note|Action):\s*(.+?)(?:\n|$)'
        ]

        for pattern in bullet_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            key_points.extend([m.strip() for m in matches if m.strip()])

        # If no bullet points found, extract key sentences
        if not key_points:
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 30]

            # Score sentences by importance indicators
            importance_words = ["must", "should", "important", "critical", "required", "ensure", "verify"]
            scored_sentences = []
            for sentence in sentences:
                score = sum(1 for word in importance_words if word.lower() in sentence.lower())
                scored_sentences.append((score, sentence))

            scored_sentences.sort(reverse=True)
            key_points = [s[1] for s in scored_sentences[:max_points]]

        return key_points[:max_points]

    def _extract_action_items(self, content: str) -> List[Dict]:
        """Extract action items from content."""
        action_items = []
        action_patterns = [
            (r'(?:please|kindly|must|should|need to)\s+(?:you\s+)?(to?\s*\w+(?:\s+\w+)*)', "request"),
            (r'(?:action|task|todo|to-do)[:\s]+(.+?)(?:\n|$)', "explicit"),
            (r'^(?:[-*•]\s*)?(?:to\s+do|action|task)[:\s]+(.+?)(?:\n|$)', "explicit")
        ]

        for pattern, item_type in action_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                action_items.append({
                    "description": match.strip(),
                    "type": item_type,
                    "status": "pending"
                })

        return action_items[:10]  # Limit to 10 action items

    def get_schema(self) -> Dict:
        """Return the skill's input schema."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "task_content": {"type": "string", "description": "Task content to summarize"},
                    "task_metadata": {"type": "object", "description": "Task metadata"},
                    "summary_type": {
                        "type": "string",
                        "enum": ["executive", "technical", "outcome"],
                        "default": "executive",
                        "description": "Type of summary to generate"
                    },
                    "max_length": {"type": "integer", "default": 500, "description": "Maximum summary length"},
                    "execution_result": {"type": "object", "description": "Execution results for outcome summaries"}
                },
                "required": ["task_content"]
            }
        }


# Register the skill
skill_registry.register(SummarizeTaskSkill())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Summarize a task")
    parser.add_argument("content", help="Task content to summarize")
    parser.add_argument("--type", choices=["executive", "technical", "outcome"], default="executive")
    parser.add_argument("--max-length", type=int, default=500)
    parser.add_argument("--metadata", type=str, help="JSON metadata (optional)")

    args = parser.parse_args()

    skill = SummarizeTaskSkill()
    context = SkillContext(
        task_id="standalone",
        task_content=args.content,
        task_metadata=json.loads(args.metadata) if args.metadata else {},
        working_directory=Path.cwd(),
        state_directory=Path.cwd() / "state",
        available_tools=[]
    )

    result = skill.execute(context, summary_type=args.type, max_length=args.max_length)
    print(json.dumps(result.to_dict(), indent=2))
