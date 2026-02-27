#!/usr/bin/env python3
"""
Claude Reasoning Loop for Silver AI Employee

Analyzes tasks using Claude AI and generates Plan.md files with execution strategies.
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
DEFAULT_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 2048

class ClaudeReasoningLoop:
    """Uses Claude AI to analyze tasks and generate execution plans."""

    def __init__(self, plans_dir: Optional[str] = None, needs_action_dir: Optional[str] = None):
        self.base_dir = Path(__file__).parent.parent.absolute()
        self.plans_dir = Path(plans_dir) if plans_dir else self.base_dir / "Plans"
        self.needs_action_dir = Path(needs_action_dir) if needs_action_dir else self.base_dir / "Needs_Action"
        self.logs_dir = self.base_dir / "logs"
        self.state_dir = self.base_dir / "state"
        
        # Ensure directories exist
        for dir_path in [self.plans_dir, self.logs_dir, self.state_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Claude API key
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        
        # State tracking
        self.processed_tasks: set = set()
        self._load_state()

    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = self.logs_dir / "claude_reasoning_log.md"
        
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
        """Load processed task IDs."""
        state_file = self.state_dir / "claude_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.processed_tasks = set(state.get("processed_tasks", []))
                    self.logger.info(f"Loaded Claude state: {len(self.processed_tasks)} processed tasks")
            except Exception as e:
                self.logger.warning(f"Could not load Claude state: {e}")

    def _save_state(self):
        """Save processed task IDs."""
        state_file = self.state_dir / "claude_state.json"
        try:
            # Keep only last 500 task IDs
            task_list = list(self.processed_tasks)[-500:]
            with open(state_file, 'w') as f:
                json.dump({"processed_tasks": task_list}, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save Claude state: {e}")

    def initialize_client(self) -> bool:
        """Initialize Anthropic Claude client."""
        try:
            if not self.api_key:
                self.logger.warning("ANTHROPIC_API_KEY not set. Using mock reasoning mode.")
                return False
            
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            self.logger.info("✅ Claude client initialized")
            return True
            
        except ImportError:
            self.logger.warning("anthropic package not installed. Using mock reasoning mode.")
            return False
        except Exception as e:
            self.logger.error(f"❌ Claude client initialization failed: {e}")
            return False

    def read_task_file(self, file_path: Path) -> Dict:
        """Read and parse a task file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata
            task_id = file_path.stem.split('_')[0] + '_' + file_path.stem.split('_')[1] if '_' in file_path.stem else file_path.stem
            
            # Try to extract structured data
            metadata = {
                'task_id': task_id,
                'file_path': str(file_path),
                'content': content,
                'source': self._detect_source(content),
                'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error reading task file: {e}")
            return {}

    def _detect_source(self, content: str) -> str:
        """Detect the source of the task."""
        content_lower = content.lower()
        if 'source: gmail' in content_lower or 'gmail' in content_lower:
            return 'gmail'
        elif 'source: whatsapp' in content_lower or 'whatsapp' in content_lower:
            return 'whatsapp'
        elif 'email' in content_lower:
            return 'email'
        elif 'source: linkedin' in content_lower:
            return 'linkedin'
        else:
            return 'manual'

    def analyze_with_claude(self, task_data: Dict) -> Dict:
        """Use Claude to analyze task and generate plan."""
        content = task_data.get('content', '')
        task_id = task_data.get('task_id', 'unknown')
        
        # Build prompt for Claude
        prompt = f"""Analyze this task and create a structured execution plan.

TASK CONTENT:
{content}

Provide your analysis in the following JSON format (no markdown, just JSON):
{{
    "category": "communication|technical|administrative|creative|analysis|other",
    "priority": "critical|high|medium|low",
    "urgency": "immediate|today|this_week|later",
    "complexity": "simple|moderate|complex",
    "estimated_effort": "5min|15min|30min|1hour|2hours|4hours|1day",
    "required_skills": ["skill1", "skill2"],
    "steps": [
        {{"step": 1, "action": "description", "estimated_time": "5min"}},
        {{"step": 2, "action": "description", "estimated_time": "10min"}}
    ],
    "risks": ["potential risk 1", "potential risk 2"],
    "dependencies": ["dependency 1", "dependency 2"],
    "success_criteria": "Clear definition of done",
    "reasoning": "Brief explanation of your analysis"
}}

Be specific and actionable. Consider:
- What type of task is this?
- How urgent and important is it?
- What skills are needed?
- What are the concrete steps to complete it?
- What could go wrong?
- What defines success?"""

        try:
            if not self.client:
                # Mock response when Claude is not available
                return self._generate_mock_analysis(task_data)
            
            response = self.client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse response
            response_text = response.content[0].text
            
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                analysis = json.loads(json_match.group())
                self.logger.info(f"✅ Claude analysis completed for {task_id}")
                return analysis
            else:
                self.logger.warning(f"Claude response not valid JSON for {task_id}")
                return self._generate_mock_analysis(task_data)
                
        except Exception as e:
            self.logger.error(f"Claude analysis failed for {task_id}: {e}")
            return self._generate_mock_analysis(task_data)

    def _generate_mock_analysis(self, task_data: Dict) -> Dict:
        """Generate a mock analysis when Claude is not available."""
        content = task_data.get('content', '').lower()
        
        # Simple rule-based analysis
        if 'email' in content or 'whatsapp' in content:
            category = 'communication'
            steps = [
                {"step": 1, "action": "Review message content", "estimated_time": "2min"},
                {"step": 2, "action": "Determine required response", "estimated_time": "3min"},
                {"step": 3, "action": "Execute response action", "estimated_time": "5min"}
            ]
            skills = ['communication', 'response_handling']
        elif 'bug' in content or 'error' in content:
            category = 'technical'
            steps = [
                {"step": 1, "action": "Reproduce the issue", "estimated_time": "10min"},
                {"step": 2, "action": "Identify root cause", "estimated_time": "15min"},
                {"step": 3, "action": "Implement fix", "estimated_time": "30min"},
                {"step": 4, "action": "Test the fix", "estimated_time": "10min"}
            ]
            skills = ['debugging', 'problem_solving']
        else:
            category = 'general'
            steps = [
                {"step": 1, "action": "Understand task requirements", "estimated_time": "5min"},
                {"step": 2, "action": "Plan approach", "estimated_time": "5min"},
                {"step": 3, "action": "Execute task", "estimated_time": "15min"}
            ]
            skills = ['general_task_management']
        
        return {
            "category": category,
            "priority": "medium",
            "urgency": "today",
            "complexity": "simple",
            "estimated_effort": "15min",
            "required_skills": skills,
            "steps": steps,
            "risks": ["Task may require additional context"],
            "dependencies": [],
            "success_criteria": "Task completed according to requirements",
            "reasoning": "Mock analysis generated (Claude API not available)"
        }

    def generate_plan_file(self, task_data: Dict, analysis: Dict) -> Optional[Path]:
        """Generate a Plan.md file for the task."""
        try:
            task_id = task_data.get('task_id', 'unknown')
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            plan_id = f"Plan-{timestamp}-{task_id[-6:] if len(task_id) > 6 else '000'}"
            
            # Build plan content
            plan_content = f"""# Execution Plan: {plan_id}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Task ID:** {task_id}
**Source:** {task_data.get('source', 'unknown')}

---

## 📊 Analysis Summary

| Attribute | Value |
|-----------|-------|
| **Category** | {analysis.get('category', 'unknown')} |
| **Priority** | {analysis.get('priority', 'medium')} |
| **Urgency** | {analysis.get('urgency', 'today')} |
| **Complexity** | {analysis.get('complexity', 'simple')} |
| **Estimated Effort** | {analysis.get('estimated_effort', 'unknown')} |

---

## 🎯 Success Criteria

{analysis.get('success_criteria', 'Task completed according to requirements')}

---

## 📋 Execution Steps

| Step | Action | Estimated Time | Status |
|------|--------|----------------|--------|
{self._format_steps_table(analysis.get('steps', []))}

---

## 🛠️ Required Skills

{self._format_skills_list(analysis.get('required_skills', []))}

---

## ⚠️ Potential Risks

{self._format_risks_list(analysis.get('risks', []))}

---

## 🔗 Dependencies

{self._format_dependencies_list(analysis.get('dependencies', []))}

---

## 🤖 AI Reasoning

{analysis.get('reasoning', 'No reasoning provided')}

---

## 📝 Execution Log

| Timestamp | Step | Status | Notes |
|-----------|------|--------|-------|
| - | - | Pending | Plan created, awaiting execution |

---

*Generated by Claude Reasoning Loop*
"""
            
            # Save plan file
            plan_file = self.plans_dir / f"{plan_id}.md"
            with open(plan_file, 'w', encoding='utf-8') as f:
                f.write(plan_content)
            
            self.logger.info(f"✅ Plan created: {plan_file.name}")
            return plan_file
            
        except Exception as e:
            self.logger.error(f"Error generating plan file: {e}")
            return None

    def _format_steps_table(self, steps: List[Dict]) -> str:
        """Format steps as markdown table rows."""
        if not steps:
            return "| 1 | No steps defined | - | ⏳ Pending |"
        
        rows = []
        for step in steps:
            step_num = step.get('step', '?')
            action = step.get('action', 'Unknown action')
            time_est = step.get('estimated_time', '?')
            rows.append(f"| {step_num} | {action} | {time_est} | ⏳ Pending |")
        
        return '\n'.join(rows)

    def _format_skills_list(self, skills: List[str]) -> str:
        """Format skills as markdown list."""
        if not skills:
            return "- No specific skills required"
        return '\n'.join(f"- 🎯 {skill}" for skill in skills)

    def _format_risks_list(self, risks: List[str]) -> str:
        """Format risks as markdown list."""
        if not risks:
            return "- No significant risks identified"
        return '\n'.join(f"- ⚠️ {risk}" for risk in risks)

    def _format_dependencies_list(self, dependencies: List[str]) -> str:
        """Format dependencies as markdown list."""
        if not dependencies:
            return "- No dependencies"
        return '\n'.join(f"- 🔗 {dep}" for dep in dependencies)

    def process_task(self, file_path: Path) -> Optional[Path]:
        """Process a single task file and generate plan."""
        try:
            task_id = file_path.stem
            
            # Skip if already processed
            if task_id in self.processed_tasks:
                self.logger.info(f"⏭️  Already processed: {task_id}")
                return None
            
            # Read task
            task_data = self.read_task_file(file_path)
            if not task_data:
                return None
            
            # Analyze with Claude
            analysis = self.analyze_with_claude(task_data)
            
            # Generate plan
            plan_file = self.generate_plan_file(task_data, analysis)
            
            if plan_file:
                # Mark as processed
                self.processed_tasks.add(task_id)
                self._save_state()
            
            return plan_file
            
        except Exception as e:
            self.logger.error(f"Error processing task: {e}")
            return None

    def process_all_pending(self) -> int:
        """Process all tasks in Needs_Action directory."""
        if not self.needs_action_dir.exists():
            return 0
        
        task_files = list(self.needs_action_dir.glob("*.md"))
        processed_count = 0
        
        for task_file in task_files:
            result = self.process_task(task_file)
            if result:
                processed_count += 1
        
        self.logger.info(f"Processed {processed_count} task(s)")
        return processed_count

    def run(self, check_interval: int = 30):
        """Run the Claude reasoning loop."""
        self.logger.info("="*60)
        self.logger.info("🤖 CLAUDE REASONING LOOP STARTED")
        self.logger.info("="*60)
        self.logger.info(f"📂 Plans Directory: {self.plans_dir}")
        self.logger.info(f"⏱️  Check Interval: {check_interval}s")
        self.logger.info("Press Ctrl+C to stop")
        self.logger.info("="*60)
        
        # Initialize client
        self.initialize_client()
        
        try:
            while True:
                # Process pending tasks
                count = self.process_all_pending()
                
                # Print status
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                      f"Claude: {count} plans | "
                      f"Total: {len(self.processed_tasks)}  ",
                      end="", flush=True)
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("\n\n Claude reasoning loop stopped by user")
        except Exception as e:
            self.logger.error(f"💥 Claude reasoning loop error: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude Reasoning Loop")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")
    parser.add_argument("--process", action="store_true", help="Process once and exit")
    
    args = parser.parse_args()
    
    reasoning = ClaudeReasoningLoop()
    reasoning.initialize_client()
    
    if args.process:
        count = reasoning.process_all_pending()
        print(f"Processed {count} task(s)")
    else:
        reasoning.run(check_interval=args.interval)


if __name__ == "__main__":
    main()
