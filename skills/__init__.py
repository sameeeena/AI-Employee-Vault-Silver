"""
Agent Skills Framework for Silver AI Employee

This module provides the base framework for all AI agent skills.
Skills are modular, reusable capabilities that the AI can invoke.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import json
from pathlib import Path
import logging


class SkillStatus(Enum):
    """Status of skill execution."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    REQUIRES_APPROVAL = "requires_approval"
    REQUIRES_INPUT = "requires_input"


@dataclass
class SkillResult:
    """Result of a skill execution."""
    status: SkillStatus
    data: Any = None
    error_message: Optional[str] = None
    requires_human_approval: bool = False
    next_action: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return {
            "status": self.status.value,
            "data": self.data,
            "error_message": self.error_message,
            "requires_human_approval": self.requires_human_approval,
            "next_action": self.next_action,
            "metadata": self.metadata
        }


@dataclass
class SkillContext:
    """Context passed to skills during execution."""
    task_id: str
    task_content: str
    task_metadata: Dict
    working_directory: Path
    state_directory: Path
    available_tools: List[str]
    execution_history: List[Dict] = field(default_factory=list)


class BaseSkill(ABC):
    """Base class for all agent skills."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"skill.{name}")

    @abstractmethod
    def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """
        Execute the skill.

        Args:
            context: The execution context
            **kwargs: Skill-specific parameters

        Returns:
            SkillResult containing the outcome
        """
        pass

    def validate_input(self, context: SkillContext, **kwargs) -> tuple[bool, str]:
        """
        Validate input before execution.

        Args:
            context: The execution context
            **kwargs: Skill-specific parameters

        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, ""

    def get_schema(self) -> Dict:
        """Return the skill's input schema."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {}
        }


class SkillRegistry:
    """Registry for managing available skills."""

    _instance = None
    _skills: Dict[str, BaseSkill] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, skill: BaseSkill):
        """Register a skill."""
        self._skills[skill.name] = skill
        self.logger.info(f"Registered skill: {skill.name}")

    def get(self, name: str) -> Optional[BaseSkill]:
        """Get a skill by name."""
        return self._skills.get(name)

    def list_skills(self) -> List[str]:
        """List all registered skill names."""
        return list(self._skills.keys())

    def get_all_schemas(self) -> List[Dict]:
        """Get schemas for all registered skills."""
        return [skill.get_schema() for skill in self._skills.values()]

    @property
    def logger(self):
        return logging.getLogger("skill.registry")


# Global registry instance
skill_registry = SkillRegistry()
