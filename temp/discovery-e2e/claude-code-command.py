#!/usr/bin/env python3
"""
Claude Code Custom Command: Multi-Agent Issue Resolution System

This command allows you to invoke the multi-agent issue resolution system
with a screenshot or error logs as the starting point.

Usage:
  python claude-code-command.py --screenshot path/to/screenshot.png
  python claude-code-command.py --logs "Error log content here"
  python claude-code-command.py --issue-description "Manual issue description"
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import uuid
import base64
import hashlib

# Import the workflow enforcement system
from workflow_enforcement_system import WorkflowEnforcementSystem, WorkflowState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IssueAnalyzer:
    """Analyzes screenshots and error logs to categorize issues"""
    
    def __init__(self):
        self.ui_keywords = [
            "button", "click", "modal", "dialog", "component", "render", "display",
            "ui", "frontend", "react", "css", "style", "layout", "responsive",
            "form", "input", "dropdown", "menu", "navigation", "page", "loading"
        ]
        
        self.backend_keywords = [
            "api", "endpoint", "server", "database", "query", "connection",
            "timeout", "error", "exception", "500", "404", "403", "401",
            "backend", "service", "request", "response", "authentication",
            "authorization", "middleware", "log", "trace", "stack"
        ]
        
        self.database_keywords = [
            "database", "sql", "query", "table", "column", "constraint",
            "migration", "schema", "foreign key", "primary key", "index",
            "postgres", "sqlite", "transaction", "commit", "rollback",
            "integrity", "constraint", "duplicate", "unique"
        ]
        
        self.architecture_keywords = [
            "architecture", "design", "pattern", "integration", "system",
            "component", "module", "dependency", "coupling", "cohesion",
            "scalability", "performance", "optimization", "refactor",
            "documentation", "api", "interface", "contract"
        ]
    
    def analyze_screenshot(self, screenshot_path: str) -> Dict:
        """Analyze screenshot to determine issue type and details"""
        if not os.path.exists(screenshot_path):
            raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")
        
        # Get file info
        file_size = os.path.getsize(screenshot_path)
        file_hash = self._get_file_hash(screenshot_path)
        
        # Encode image for analysis
        with open(screenshot_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        # Analyze filename for clues
        filename = os.path.basename(screenshot_path).lower()
        
        # Determine likely issue type based on filename
        issue_type = "ui"  # Default for screenshots
        confidence = 0.8
        
        if any(keyword in filename for keyword in ["error", "bug", "issue", "problem"]):
            confidence = 0.9
        
        return {
            "issue_type": issue_type,
            "confidence": confidence,
            "source_type": "screenshot",
            "source_path": screenshot_path,
            "file_size": file_size,
            "file_hash": file_hash,
            "analysis_method": "filename_analysis",
            "image_data": image_data[:100] + "..." if len(image_data) > 100 else image_data,  # Truncate for display
            "suggested_reporter": "agent-1",  # UI issues typically reported by Agent-1
            "description": f"UI issue identified from screenshot: {filename}"
        }
    
    def analyze_error_logs(self, error_logs: str) -> Dict:
        """Analyze error logs to determine issue type and details"""
        logs_lower = error_logs.lower()
        
        # Score each category
        ui_score = sum(1 for keyword in self.ui_keywords if keyword in logs_lower)
        backend_score = sum(1 for keyword in self.backend_keywords if keyword in logs_lower)
        database_score = sum(1 for keyword in self.database_keywords if keyword in logs_lower)
        architecture_score = sum(1 for keyword in self.architecture_keywords if keyword in logs_lower)
        
        # Determine issue type
        scores = {
            "ui": ui_score,
            "backend": backend_score,
            "database": database_score,
            "architecture": architecture_score
        }
        
        issue_type = max(scores, key=scores.get)
        confidence = scores[issue_type] / max(sum(scores.values()), 1)
        
        # Determine suggested reporter based on issue type
        reporter_mapping = {
            "ui": "agent-1",
            "backend": "agent-2",
            "database": "agent-3",
            "architecture": "agent-4"
        }
        
        suggested_reporter = reporter_mapping.get(issue_type, "agent-1")
        
        return {
            "issue_type": issue_type,
            "confidence": confidence,
            "source_type": "error_logs",
            "source_content": error_logs,
            "analysis_method": "keyword_analysis",
            "scores": scores,
            "suggested_reporter": suggested_reporter,
            "description": f"{issue_type.capitalize()} issue identified from error logs"
        }
    
    def analyze_manual_description(self, description: str) -> Dict:
        """Analyze manual issue description"""
        desc_lower = description.lower()
        
        # Score each category
        ui_score = sum(1 for keyword in self.ui_keywords if keyword in desc_lower)
        backend_score = sum(1 for keyword in self.backend_keywords if keyword in desc_lower)
        database_score = sum(1 for keyword in self.database_keywords if keyword in desc_lower)
        architecture_score = sum(1 for keyword in self.architecture_keywords if keyword in desc_lower)
        
        # Determine issue type
        scores = {
            "ui": ui_score,
            "backend": backend_score,
            "database": database_score,
            "architecture": architecture_score
        }
        
        issue_type = max(scores, key=scores.get)
        confidence = scores[issue_type] / max(sum(scores.values()), 1)
        
        if confidence == 0:
            issue_type = "ui"  # Default
            confidence = 0.3
        
        # Determine suggested reporter
        reporter_mapping = {
            "ui": "agent-1",
            "backend": "agent-2",
            "database": "agent-3",
            "architecture": "agent-4"
        }
        
        suggested_reporter = reporter_mapping.get(issue_type, "agent-1")
        
        return {
            "issue_type": issue_type,
            "confidence": confidence,
            "source_type": "manual_description",
            "source_content": description,
            "analysis_method": "keyword_analysis",
            "scores": scores,
            "suggested_reporter": suggested_reporter,
            "description": description
        }
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate hash for file"""
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()


class MultiAgentIssueResolutionSystem:
    """Main system for multi-agent issue resolution"""
    
    def __init__(self):
        self.analyzer = IssueAnalyzer()
        self.workflow_system = WorkflowEnforcementSystem()
        self.issue_counter = 1
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Agent mapping
        self.agent_mapping = {
            "ui": "agent-1",
            "backend": "agent-2", 
            "database": "agent-3",
            "architecture": "agent-4"
        }
        
        # Create session directory
        self.session_dir = f"/Users/chocka/CursorProjects/migrate-ui-orchestrator/temp/discovery-e2e/session_{self.session_id}"
        os.makedirs(self.session_dir, exist_ok=True)
        
        logger.info("🚀 Multi-Agent Issue Resolution System initialized")
        logger.info(f"📁 Session directory: {self.session_dir}")
    
    def process_screenshot(self, screenshot_path: str) -> str:
        """Process screenshot and create issue"""
        logger.info(f"🖼️ Processing screenshot: {screenshot_path}")
        
        # Analyze screenshot
        analysis = self.analyzer.analyze_screenshot(screenshot_path)
        
        # Generate issue ID
        issue_id = f"ISSUE-{self.session_id}-{self.issue_counter:03d}"
        self.issue_counter += 1
        
        # Create issue
        issue_data = self._create_issue(issue_id, analysis)
        
        # Register with workflow system
        self.workflow_system.register_issue(
            issue_id=issue_id,
            agent_id="agent-8",  # Implementation agent
            original_reporter=analysis["suggested_reporter"]
        )
        
        # Save issue data
        self._save_issue_data(issue_id, issue_data)
        
        # Copy screenshot to session directory
        screenshot_copy = os.path.join(self.session_dir, f"{issue_id}_screenshot.png")
        import shutil
        shutil.copy2(screenshot_path, screenshot_copy)
        
        logger.info(f"✅ Created issue {issue_id} from screenshot")
        return issue_id
    
    def process_error_logs(self, error_logs: str) -> str:
        """Process error logs and create issue"""
        logger.info(f"📋 Processing error logs ({len(error_logs)} characters)")
        
        # Analyze error logs
        analysis = self.analyzer.analyze_error_logs(error_logs)
        
        # Generate issue ID
        issue_id = f"ISSUE-{self.session_id}-{self.issue_counter:03d}"
        self.issue_counter += 1
        
        # Create issue
        issue_data = self._create_issue(issue_id, analysis)
        
        # Register with workflow system
        self.workflow_system.register_issue(
            issue_id=issue_id,
            agent_id="agent-8",  # Implementation agent
            original_reporter=analysis["suggested_reporter"]
        )
        
        # Save issue data
        self._save_issue_data(issue_id, issue_data)
        
        # Save error logs
        logs_file = os.path.join(self.session_dir, f"{issue_id}_error_logs.txt")
        with open(logs_file, "w") as f:
            f.write(error_logs)
        
        logger.info(f"✅ Created issue {issue_id} from error logs")
        return issue_id
    
    def process_manual_description(self, description: str) -> str:
        """Process manual issue description"""
        logger.info(f"✍️ Processing manual description ({len(description)} characters)")
        
        # Analyze description
        analysis = self.analyzer.analyze_manual_description(description)
        
        # Generate issue ID
        issue_id = f"ISSUE-{self.session_id}-{self.issue_counter:03d}"
        self.issue_counter += 1
        
        # Create issue
        issue_data = self._create_issue(issue_id, analysis)
        
        # Register with workflow system
        self.workflow_system.register_issue(
            issue_id=issue_id,
            agent_id="agent-8",  # Implementation agent
            original_reporter=analysis["suggested_reporter"]
        )
        
        # Save issue data
        self._save_issue_data(issue_id, issue_data)
        
        logger.info(f"✅ Created issue {issue_id} from manual description")
        return issue_id
    
    def _create_issue(self, issue_id: str, analysis: Dict) -> Dict:
        """Create issue data structure"""
        return {
            "issue_id": issue_id,
            "created_at": datetime.now().isoformat(),
            "session_id": self.session_id,
            "analysis": analysis,
            "workflow_state": "IDENTIFIED",
            "priority": self._determine_priority(analysis),
            "estimated_effort": self._estimate_effort(analysis),
            "suggested_agents": self._suggest_agents(analysis),
            "next_steps": self._generate_next_steps(analysis)
        }
    
    def _determine_priority(self, analysis: Dict) -> str:
        """Determine issue priority"""
        if analysis["issue_type"] == "ui" and analysis["confidence"] > 0.8:
            return "high"  # UI issues are user-facing
        elif analysis["issue_type"] == "backend" and "error" in analysis.get("source_content", "").lower():
            return "high"  # Backend errors are critical
        elif analysis["issue_type"] == "database":
            return "medium"  # Database issues need careful handling
        else:
            return "medium"
    
    def _estimate_effort(self, analysis: Dict) -> str:
        """Estimate effort required"""
        if analysis["confidence"] > 0.8:
            return "medium"  # Clear issues are easier to fix
        elif analysis["issue_type"] == "architecture":
            return "high"  # Architecture changes are complex
        else:
            return "medium"
    
    def _suggest_agents(self, analysis: Dict) -> List[str]:
        """Suggest agents for the issue"""
        primary_agent = analysis["suggested_reporter"]
        
        # Always include implementation agent
        agents = ["agent-8"]
        
        # Add original reporter
        if primary_agent not in agents:
            agents.append(primary_agent)
        
        # Add verification agent
        if "agent-7" not in agents:
            agents.append("agent-7")
        
        # Add historical review agent
        if "agent-5" not in agents:
            agents.append("agent-5")
        
        return agents
    
    def _generate_next_steps(self, analysis: Dict) -> List[str]:
        """Generate next steps for the issue"""
        steps = [
            "1. Agent-5 performs historical review for similar issues",
            f"2. {analysis['suggested_reporter']} validates issue reproduction",
            "3. Agent-4 documents solution approach",
            "4. Agent-8 implements the solution",
            "5. Agent-7 verifies implementation",
            f"6. {analysis['suggested_reporter']} validates resolution",
            "7. Issue marked as completed"
        ]
        return steps
    
    def _save_issue_data(self, issue_id: str, issue_data: Dict):
        """Save issue data to file"""
        issue_file = os.path.join(self.session_dir, f"{issue_id}.json")
        with open(issue_file, "w") as f:
            json.dump(issue_data, f, indent=2)
    
    def launch_agents(self, issue_id: str) -> Dict:
        """Launch multi-agent resolution process"""
        logger.info(f"🚀 Launching multi-agent resolution for {issue_id}")
        
        # Load issue data
        issue_file = os.path.join(self.session_dir, f"{issue_id}.json")
        with open(issue_file, "r") as f:
            issue_data = json.load(f)
        
        # Create agent execution plan
        execution_plan = {
            "issue_id": issue_id,
            "execution_start": datetime.now().isoformat(),
            "agents": {
                "agent-5": {
                    "role": "Historical Review",
                    "status": "pending",
                    "task": "Review historical similar issues and solutions"
                },
                issue_data["analysis"]["suggested_reporter"]: {
                    "role": "Original Reporter",
                    "status": "pending", 
                    "task": "Validate issue reproduction and eventual resolution"
                },
                "agent-4": {
                    "role": "Solution Architect",
                    "status": "pending",
                    "task": "Document solution approach and design"
                },
                "agent-8": {
                    "role": "Implementation",
                    "status": "pending",
                    "task": "Implement the solution"
                },
                "agent-7": {
                    "role": "Verification",
                    "status": "pending",
                    "task": "Verify implementation quality and completeness"
                }
            },
            "workflow_transitions": []
        }
        
        # Save execution plan
        plan_file = os.path.join(self.session_dir, f"{issue_id}_execution_plan.json")
        with open(plan_file, "w") as f:
            json.dump(execution_plan, f, indent=2)
        
        # Create agent instructions
        self._create_agent_instructions(issue_id, issue_data)
        
        logger.info(f"✅ Multi-agent resolution launched for {issue_id}")
        return execution_plan
    
    def _create_agent_instructions(self, issue_id: str, issue_data: Dict):
        """Create specific instructions for each agent"""
        instructions_dir = os.path.join(self.session_dir, "agent_instructions")
        os.makedirs(instructions_dir, exist_ok=True)
        
        # Agent-5 (Historical Review)
        with open(os.path.join(instructions_dir, f"{issue_id}_agent-5_instructions.md"), "w") as f:
            f.write(f"""# Agent-5 Historical Review Instructions - {issue_id}

## Issue Summary
- **Issue ID**: {issue_id}
- **Type**: {issue_data['analysis']['issue_type']}
- **Confidence**: {issue_data['analysis']['confidence']:.2f}
- **Description**: {issue_data['analysis']['description']}

## Your Task
1. Search for similar issues in the codebase and documentation
2. Review previous solutions for comparable problems
3. Identify potential code patterns or anti-patterns
4. Document historical context and lessons learned
5. Recommend approach based on historical analysis

## Expected Deliverables
- Historical review document
- Recommendations for solution approach
- Potential pitfalls to avoid
- Timeline estimate based on historical similar issues

## Next Steps
After completing historical review, transition issue to SOLUTION_APPROVED state.
""")
        
        # Original Reporter Instructions
        reporter_agent = issue_data["analysis"]["suggested_reporter"]
        with open(os.path.join(instructions_dir, f"{issue_id}_{reporter_agent}_instructions.md"), "w") as f:
            f.write(f"""# {reporter_agent} Original Reporter Instructions - {issue_id}

## Issue Summary
- **Issue ID**: {issue_id}
- **Type**: {issue_data['analysis']['issue_type']}
- **Source**: {issue_data['analysis']['source_type']}
- **Description**: {issue_data['analysis']['description']}

## Your Task as Original Reporter
1. **Initial Validation**: Reproduce the issue if possible
2. **Context Provision**: Provide additional context about the issue
3. **Solution Validation**: After implementation, validate the fix works
4. **Final Approval**: Confirm the issue is fully resolved

## Validation Requirements
- Test the original scenario that caused the issue
- Verify the fix doesn't break existing functionality
- Confirm user experience is improved
- Document specific validation steps performed

## Expected Deliverables
- Issue reproduction confirmation
- Validation report after implementation
- Final approval for issue closure

## Next Steps
After implementation, you must validate the resolution before issue can be marked COMPLETED.
""")
        
        # Agent-4 (Solution Architect)
        with open(os.path.join(instructions_dir, f"{issue_id}_agent-4_instructions.md"), "w") as f:
            f.write(f"""# Agent-4 Solution Architect Instructions - {issue_id}

## Issue Summary
- **Issue ID**: {issue_id}
- **Type**: {issue_data['analysis']['issue_type']}
- **Priority**: {issue_data['priority']}
- **Estimated Effort**: {issue_data['estimated_effort']}

## Your Task
1. Design solution approach based on historical review
2. Consider architectural implications
3. Plan implementation steps
4. Document solution architecture
5. Review and approve final implementation

## Expected Deliverables
- Solution approach document
- Architecture design (if needed)
- Implementation plan
- Review of implemented solution

## Next Steps
After documenting solution approach, transition issue to IMPLEMENTATION state.
""")
        
        # Agent-8 (Implementation)
        with open(os.path.join(instructions_dir, f"{issue_id}_agent-8_instructions.md"), "w") as f:
            f.write(f"""# Agent-8 Implementation Instructions - {issue_id}

## Issue Summary
- **Issue ID**: {issue_id}
- **Type**: {issue_data['analysis']['issue_type']}
- **Solution Type**: {issue_data['analysis']['suggested_reporter']} issue

## Your Task
1. Implement solution based on architect's design
2. Follow coding standards and patterns
3. Test implementation thoroughly
4. Document code changes
5. Prepare for verification

## Expected Deliverables
- Code implementation
- Unit tests (if applicable)
- Documentation of changes
- Implementation summary

## Next Steps
After implementation, hand off to Agent-7 for verification.
""")
        
        # Agent-7 (Verification)
        with open(os.path.join(instructions_dir, f"{issue_id}_agent-7_instructions.md"), "w") as f:
            f.write(f"""# Agent-7 Verification Instructions - {issue_id}

## Issue Summary
- **Issue ID**: {issue_id}
- **Implementation Agent**: Agent-8
- **Original Reporter**: {reporter_agent}

## Your Task
1. Verify implementation quality
2. Test functionality thoroughly
3. Check code standards compliance
4. Validate against requirements
5. Prepare for original reporter validation

## Expected Deliverables
- Verification report
- Test results
- Quality assessment
- Handoff to original reporter

## Next Steps
After verification, transition to ORIGINAL_REPORTER_VALIDATION state.
""")
    
    def get_status(self, issue_id: str) -> Dict:
        """Get current status of issue resolution"""
        issue_file = os.path.join(self.session_dir, f"{issue_id}.json")
        if not os.path.exists(issue_file):
            return {"error": f"Issue {issue_id} not found"}
        
        with open(issue_file, "r") as f:
            issue_data = json.load(f)
        
        # Get workflow status
        workflow_issue = self.workflow_system.issues.get(issue_id)
        if workflow_issue:
            current_state = workflow_issue.current_state.value
            transitions = [
                {
                    "from": t.from_state.value,
                    "to": t.to_state.value,
                    "timestamp": t.timestamp.isoformat(),
                    "agent": t.agent_id
                }
                for t in workflow_issue.transitions
            ]
        else:
            current_state = "not_registered"
            transitions = []
        
        return {
            "issue_id": issue_id,
            "current_state": current_state,
            "created_at": issue_data["created_at"],
            "issue_type": issue_data["analysis"]["issue_type"],
            "priority": issue_data["priority"],
            "transitions": transitions,
            "session_dir": self.session_dir
        }


def main():
    """Main command line interface"""
    parser = argparse.ArgumentParser(description="Multi-Agent Issue Resolution System")
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--screenshot", help="Path to screenshot file")
    input_group.add_argument("--logs", help="Error logs content")
    input_group.add_argument("--description", help="Manual issue description")
    
    # Action options
    parser.add_argument("--launch", action="store_true", help="Launch agents after creating issue")
    parser.add_argument("--status", help="Get status of existing issue by ID")
    
    args = parser.parse_args()
    
    # Initialize system
    system = MultiAgentIssueResolutionSystem()
    
    # Handle status check
    if args.status:
        status = system.get_status(args.status)
        print(json.dumps(status, indent=2))
        return
    
    # Process input and create issue
    issue_id = None
    
    if args.screenshot:
        issue_id = system.process_screenshot(args.screenshot)
    elif args.logs:
        issue_id = system.process_error_logs(args.logs)
    elif args.description:
        issue_id = system.process_manual_description(args.description)
    
    if issue_id:
        print(f"✅ Created issue: {issue_id}")
        
        # Launch agents if requested
        if args.launch:
            execution_plan = system.launch_agents(issue_id)
            print("🚀 Launched multi-agent resolution")
            print(f"📁 Session directory: {system.session_dir}")
            
            # Show next steps
            print("\n📋 Next Steps:")
            print("1. Review agent instructions in session directory")
            print("2. Agents will follow the workflow enforcement system")
            print("3. Use --status to check progress")
            
        else:
            print("💡 Use --launch to start multi-agent resolution")
            print(f"💡 Use --status {issue_id} to check status")


if __name__ == "__main__":
    main()