#!/usr/bin/env python3
"""
Discovery Flow E2E - Workflow Enforcement System

This system enforces proper workflow compliance for issue resolution
to prevent the 91.7% non-compliance rate identified in the audit.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, asdict
import os
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowState(Enum):
    """Valid workflow states for issue resolution"""
    IDENTIFIED = "identified"
    HISTORICAL_REVIEW = "historical_review"
    SOLUTION_APPROVED = "solution_approved"
    IMPLEMENTATION = "implementation"
    VERIFICATION = "verification"
    ORIGINAL_REPORTER_VALIDATION = "original_reporter_validation"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class ComplianceViolation(Enum):
    """Types of compliance violations"""
    MISSING_HISTORICAL_REVIEW = "missing_historical_review"
    MISSING_SOLUTION_APPROACH = "missing_solution_approach"
    IMPLEMENTATION_WITHOUT_APPROVAL = "implementation_without_approval"
    MISSING_VERIFICATION = "missing_verification"
    MISSING_RESOLUTION_DETAILS = "missing_resolution_details"
    INVALID_STATE_TRANSITION = "invalid_state_transition"
    MISSING_DOCUMENTATION = "missing_documentation"
    MISSING_ORIGINAL_REPORTER_VALIDATION = "missing_original_reporter_validation"
    WRONG_VALIDATOR_AGENT = "wrong_validator_agent"


@dataclass
class WorkflowTransition:
    """Represents a state transition in the workflow"""
    from_state: WorkflowState
    to_state: WorkflowState
    timestamp: datetime
    agent_id: str
    validation_passed: bool
    notes: Optional[str] = None


@dataclass
class IssueTracking:
    """Comprehensive issue tracking with compliance monitoring"""
    issue_id: str
    current_state: WorkflowState
    created_at: datetime
    updated_at: datetime
    agent_assigned: Optional[str] = None
    original_reporter_agent: Optional[str] = None  # Agent who originally reported the issue
    historical_review_completed: bool = False
    solution_approach_documented: bool = False
    implementation_verified: bool = False
    resolution_documented: bool = False
    original_reporter_validated: bool = False  # Original reporter confirmed fix
    validation_details: Optional[str] = None  # Details of validation performed
    transitions: List[WorkflowTransition] = None
    violations: List[ComplianceViolation] = None
    
    def __post_init__(self):
        if self.transitions is None:
            self.transitions = []
        if self.violations is None:
            self.violations = []


class WorkflowEnforcementSystem:
    """Main workflow enforcement system"""
    
    def __init__(self, config_path: str = "workflow-config.json"):
        self.config_path = config_path
        self.issues: Dict[str, IssueTracking] = {}
        self.valid_transitions = self._define_valid_transitions()
        self.load_configuration()
        
    def _define_valid_transitions(self) -> Dict[WorkflowState, List[WorkflowState]]:
        """Define valid state transitions"""
        return {
            WorkflowState.IDENTIFIED: [
                WorkflowState.HISTORICAL_REVIEW,
                WorkflowState.BLOCKED
            ],
            WorkflowState.HISTORICAL_REVIEW: [
                WorkflowState.SOLUTION_APPROVED,
                WorkflowState.BLOCKED
            ],
            WorkflowState.SOLUTION_APPROVED: [
                WorkflowState.IMPLEMENTATION,
                WorkflowState.BLOCKED
            ],
            WorkflowState.IMPLEMENTATION: [
                WorkflowState.VERIFICATION,
                WorkflowState.BLOCKED
            ],
            WorkflowState.VERIFICATION: [
                WorkflowState.ORIGINAL_REPORTER_VALIDATION,
                WorkflowState.IMPLEMENTATION,  # Back to implementation if verification fails
                WorkflowState.BLOCKED
            ],
            WorkflowState.ORIGINAL_REPORTER_VALIDATION: [
                WorkflowState.COMPLETED,
                WorkflowState.IMPLEMENTATION,  # Back to implementation if validation fails
                WorkflowState.BLOCKED
            ],
            WorkflowState.COMPLETED: [],  # Terminal state
            WorkflowState.BLOCKED: [
                WorkflowState.HISTORICAL_REVIEW,
                WorkflowState.SOLUTION_APPROVED,
                WorkflowState.IMPLEMENTATION,
                WorkflowState.VERIFICATION,
                WorkflowState.ORIGINAL_REPORTER_VALIDATION
            ]
        }
    
    def load_configuration(self):
        """Load workflow configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    logger.info(f"✅ Loaded workflow configuration from {self.config_path}")
            else:
                logger.info("📝 Creating default workflow configuration")
                self.create_default_config()
        except Exception as e:
            logger.error(f"❌ Error loading configuration: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """Create default workflow configuration"""
        default_config = {
            "enforcement_enabled": True,
            "require_historical_review": True,
            "require_solution_documentation": True,
            "require_implementation_verification": True,
            "require_resolution_documentation": True,
            "require_original_reporter_validation": True,
            "allowed_agents": ["agent-1", "agent-2", "agent-3", "agent-4", "agent-5", "agent-6", "agent-7", "agent-8"],
            "documentation_patterns": {
                "solution_approach": "solution-approach.md",
                "resolution_details": "resolution.md",
                "historical_review": "historical-review-*.md"
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        logger.info(f"✅ Created default configuration at {self.config_path}")
    
    def register_issue(self, issue_id: str, agent_id: str, original_reporter: str = None) -> bool:
        """Register a new issue for tracking"""
        if issue_id in self.issues:
            logger.warning(f"⚠️ Issue {issue_id} already registered")
            return False
        
        # If no original reporter specified, assume the registering agent is the original reporter
        if original_reporter is None:
            original_reporter = agent_id
        
        self.issues[issue_id] = IssueTracking(
            issue_id=issue_id,
            current_state=WorkflowState.IDENTIFIED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            agent_assigned=agent_id,
            original_reporter_agent=original_reporter
        )
        
        logger.info(f"✅ Registered issue {issue_id} assigned to {agent_id}, original reporter: {original_reporter}")
        return True
    
    def request_state_transition(
        self, 
        issue_id: str, 
        new_state: WorkflowState, 
        agent_id: str,
        notes: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """Request a state transition with compliance checking"""
        
        if issue_id not in self.issues:
            return False, [f"Issue {issue_id} not found"]
        
        issue = self.issues[issue_id]
        current_state = issue.current_state
        
        # Check if transition is valid
        if new_state not in self.valid_transitions.get(current_state, []):
            violation = ComplianceViolation.INVALID_STATE_TRANSITION
            issue.violations.append(violation)
            return False, [f"Invalid transition from {current_state.value} to {new_state.value}"]
        
        # Special validation for original reporter validation state
        if new_state == WorkflowState.ORIGINAL_REPORTER_VALIDATION:
            if agent_id != issue.original_reporter_agent:
                violation = ComplianceViolation.WRONG_VALIDATOR_AGENT
                issue.violations.append(violation)
                return False, [f"Only the original reporter ({issue.original_reporter_agent}) can validate the resolution, not {agent_id}"]
        
        # Check compliance requirements
        compliance_errors = self._check_compliance_requirements(issue, new_state)
        if compliance_errors:
            return False, compliance_errors
        
        # Execute transition
        transition = WorkflowTransition(
            from_state=current_state,
            to_state=new_state,
            timestamp=datetime.utcnow(),
            agent_id=agent_id,
            validation_passed=True,
            notes=notes
        )
        
        issue.transitions.append(transition)
        issue.current_state = new_state
        issue.updated_at = datetime.utcnow()
        
        logger.info(f"✅ {issue_id}: {current_state.value} → {new_state.value} by {agent_id}")
        return True, []
    
    def _check_compliance_requirements(
        self, 
        issue: IssueTracking, 
        new_state: WorkflowState
    ) -> List[str]:
        """Check compliance requirements for state transition"""
        errors = []
        
        # Historical review required before solution approval
        if new_state == WorkflowState.SOLUTION_APPROVED:
            if not issue.historical_review_completed:
                errors.append("Historical review must be completed before solution approval")
                issue.violations.append(ComplianceViolation.MISSING_HISTORICAL_REVIEW)
        
        # Solution approach required before implementation
        if new_state == WorkflowState.IMPLEMENTATION:
            if not issue.solution_approach_documented:
                errors.append("Solution approach must be documented before implementation")
                issue.violations.append(ComplianceViolation.MISSING_SOLUTION_APPROACH)
        
        # Original reporter validation required before completion
        if new_state == WorkflowState.COMPLETED:
            if not issue.original_reporter_validated:
                errors.append("Original reporter must validate the resolution before completion")
                issue.violations.append(ComplianceViolation.MISSING_ORIGINAL_REPORTER_VALIDATION)
            
            if not issue.implementation_verified:
                errors.append("Implementation must be verified before completion")
                issue.violations.append(ComplianceViolation.MISSING_VERIFICATION)
            
            if not issue.resolution_documented:
                errors.append("Resolution details must be documented before completion")
                issue.violations.append(ComplianceViolation.MISSING_RESOLUTION_DETAILS)
        
        return errors
    
    def mark_historical_review_complete(self, issue_id: str, agent_id: str) -> bool:
        """Mark historical review as completed"""
        if issue_id not in self.issues:
            return False
        
        issue = self.issues[issue_id]
        issue.historical_review_completed = True
        issue.updated_at = datetime.utcnow()
        
        logger.info(f"✅ Historical review completed for {issue_id} by {agent_id}")
        return True
    
    def mark_solution_documented(self, issue_id: str, agent_id: str) -> bool:
        """Mark solution approach as documented"""
        if issue_id not in self.issues:
            return False
        
        issue = self.issues[issue_id]
        issue.solution_approach_documented = True
        issue.updated_at = datetime.utcnow()
        
        logger.info(f"✅ Solution approach documented for {issue_id} by {agent_id}")
        return True
    
    def mark_implementation_verified(self, issue_id: str, agent_id: str) -> bool:
        """Mark implementation as verified"""
        if issue_id not in self.issues:
            return False
        
        issue = self.issues[issue_id]
        issue.implementation_verified = True
        issue.updated_at = datetime.utcnow()
        
        logger.info(f"✅ Implementation verified for {issue_id} by {agent_id}")
        return True
    
    def mark_resolution_documented(self, issue_id: str, agent_id: str) -> bool:
        """Mark resolution as documented"""
        if issue_id not in self.issues:
            return False
        
        issue = self.issues[issue_id]
        issue.resolution_documented = True
        issue.updated_at = datetime.utcnow()
        
        logger.info(f"✅ Resolution documented for {issue_id} by {agent_id}")
        return True
    
    def mark_original_reporter_validation_complete(
        self, 
        issue_id: str, 
        agent_id: str, 
        validation_details: str
    ) -> bool:
        """Mark original reporter validation as completed"""
        if issue_id not in self.issues:
            logger.error(f"❌ Issue {issue_id} not found")
            return False
        
        issue = self.issues[issue_id]
        
        # Verify that the validating agent is the original reporter
        if agent_id != issue.original_reporter_agent:
            logger.error(f"❌ Only the original reporter ({issue.original_reporter_agent}) can validate {issue_id}, not {agent_id}")
            return False
        
        # Verify that the issue is in the correct state
        if issue.current_state != WorkflowState.ORIGINAL_REPORTER_VALIDATION:
            logger.error(f"❌ Issue {issue_id} is not in ORIGINAL_REPORTER_VALIDATION state (current: {issue.current_state.value})")
            return False
        
        issue.original_reporter_validated = True
        issue.validation_details = validation_details
        issue.updated_at = datetime.utcnow()
        
        logger.info(f"✅ Original reporter validation completed for {issue_id} by {agent_id}")
        logger.info(f"📋 Validation details: {validation_details}")
        return True
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        total_issues = len(self.issues)
        if total_issues == 0:
            return {"total_issues": 0, "compliance_rate": 0.0}
        
        compliant_issues = 0
        violation_counts = {}
        
        for issue in self.issues.values():
            if len(issue.violations) == 0:
                compliant_issues += 1
            
            for violation in issue.violations:
                violation_counts[violation.value] = violation_counts.get(violation.value, 0) + 1
        
        compliance_rate = (compliant_issues / total_issues) * 100
        
        return {
            "total_issues": total_issues,
            "compliant_issues": compliant_issues,
            "compliance_rate": compliance_rate,
            "violation_counts": violation_counts,
            "issues_by_state": self._get_issues_by_state(),
            "agent_performance": self._get_agent_performance()
        }
    
    def _get_issues_by_state(self) -> Dict[str, int]:
        """Get issue count by state"""
        state_counts = {}
        for issue in self.issues.values():
            state = issue.current_state.value
            state_counts[state] = state_counts.get(state, 0) + 1
        return state_counts
    
    def _get_agent_performance(self) -> Dict[str, Dict[str, int]]:
        """Get agent performance metrics"""
        agent_metrics = {}
        
        for issue in self.issues.values():
            if issue.agent_assigned:
                agent = issue.agent_assigned
                if agent not in agent_metrics:
                    agent_metrics[agent] = {
                        "total_issues": 0,
                        "completed_issues": 0,
                        "violations": 0
                    }
                
                agent_metrics[agent]["total_issues"] += 1
                if issue.current_state == WorkflowState.COMPLETED:
                    agent_metrics[agent]["completed_issues"] += 1
                agent_metrics[agent]["violations"] += len(issue.violations)
        
        return agent_metrics
    
    def export_tracking_data(self, filename: str = "workflow-tracking-export.json"):
        """Export all tracking data"""
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "issues": {}
        }
        
        for issue_id, issue in self.issues.items():
            export_data["issues"][issue_id] = {
                "issue_id": issue.issue_id,
                "current_state": issue.current_state.value,
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
                "agent_assigned": issue.agent_assigned,
                "original_reporter_agent": issue.original_reporter_agent,
                "historical_review_completed": issue.historical_review_completed,
                "solution_approach_documented": issue.solution_approach_documented,
                "implementation_verified": issue.implementation_verified,
                "resolution_documented": issue.resolution_documented,
                "original_reporter_validated": issue.original_reporter_validated,
                "validation_details": issue.validation_details,
                "transitions": [
                    {
                        "from_state": t.from_state.value,
                        "to_state": t.to_state.value,
                        "timestamp": t.timestamp.isoformat(),
                        "agent_id": t.agent_id,
                        "validation_passed": t.validation_passed,
                        "notes": t.notes
                    }
                    for t in issue.transitions
                ],
                "violations": [v.value for v in issue.violations]
            }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"✅ Exported tracking data to {filename}")
        return filename


def main():
    """Main function to demonstrate workflow enforcement system"""
    print("🚀 Discovery Flow E2E - Workflow Enforcement System")
    print("=" * 60)
    
    # Initialize system
    enforcement_system = WorkflowEnforcementSystem()
    
    # Example usage with existing issues
    issues = [
        "DISC-002", "DISC-003", "DISC-005", "DISC-006",
        "DISC-007", "DISC-008", "DISC-009", "DISC-010"
    ]
    
    # Register issues with original reporters
    # UI issues typically reported by Agent-1, others by various agents
    issue_reporters = {
        "DISC-002": "agent-2",  # Backend monitoring agent
        "DISC-003": "agent-3",  # Database validation agent
        "DISC-005": "agent-4",  # Solution architect
        "DISC-006": "agent-2",  # Backend monitoring agent
        "DISC-007": "agent-1",  # UI testing agent
        "DISC-008": "agent-2",  # Backend monitoring agent
        "DISC-009": "agent-2",  # Backend monitoring agent
        "DISC-010": "agent-4",  # Solution architect
    }
    
    for issue_id in issues:
        original_reporter = issue_reporters.get(issue_id, "agent-1")
        enforcement_system.register_issue(issue_id, "agent-8", original_reporter)
    
    # Simulate compliance checking
    print("\n📋 Compliance Report:")
    report = enforcement_system.get_compliance_report()
    print(f"Total Issues: {report['total_issues']}")
    print(f"Compliance Rate: {report['compliance_rate']:.1f}%")
    
    # Export tracking data
    enforcement_system.export_tracking_data()
    
    print("\n✅ Workflow enforcement system ready for deployment")
    print("💡 Agents must now follow proper workflow transitions")
    print("📊 Compliance monitoring active")


if __name__ == "__main__":
    main()