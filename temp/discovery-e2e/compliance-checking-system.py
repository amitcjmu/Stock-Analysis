#!/usr/bin/env python3
"""
Multi-Agent Workflow Compliance Checking System
Ensures all issues follow the proper workflow sequence
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class ComplianceChecker:
    def __init__(self, workflow_file: str):
        self.workflow_file = workflow_file
        self.workflow_data = self.load_workflow_data()
        self.required_states = [
            "issue_discovered",
            "solution_design", 
            "historical_review",
            "approved",
            "implementation",
            "verification",
            "documentation",
            "completed"
        ]
        
    def load_workflow_data(self) -> Dict:
        """Load the workflow tracking data"""
        with open(self.workflow_file, 'r') as f:
            return json.load(f)
    
    def check_issue_compliance(self, issue_id: str) -> Tuple[bool, List[str]]:
        """Check if an issue followed the proper workflow"""
        violations = []
        
        if issue_id not in self.workflow_data['issue_tracking']:
            return False, ["Issue not found in tracking system"]
        
        issue_data = self.workflow_data['issue_tracking'][issue_id]
        state_history = issue_data['state_history']
        
        # Extract states in order
        states_visited = [entry['state'] for entry in state_history]
        
        # Check 1: All required states visited (except completed)
        required_before_complete = self.required_states[:-1]
        for required_state in required_before_complete:
            if required_state not in states_visited:
                if not (required_state == "approved" and "historical_review" in states_visited):
                    violations.append(f"skipped_{required_state}")
        
        # Check 2: States visited in correct order
        state_indices = {}
        for i, state in enumerate(states_visited):
            if state not in state_indices:
                state_indices[state] = i
        
        # Verify sequence
        if 'solution_design' in state_indices and 'issue_discovered' in state_indices:
            if state_indices['solution_design'] < state_indices['issue_discovered']:
                violations.append("out_of_order_solution_design")
        
        if 'historical_review' in state_indices and 'solution_design' in state_indices:
            if state_indices['historical_review'] < state_indices['solution_design']:
                violations.append("out_of_order_historical_review")
                
        if 'implementation' in state_indices:
            if 'approved' not in state_indices and 'historical_review' not in state_indices:
                violations.append("implemented_without_approval")
            elif 'approved' in state_indices and state_indices['implementation'] < state_indices['approved']:
                violations.append("implemented_before_approval")
        
        # Check 3: Documentation completeness
        docs = issue_data.get('documentation', {})
        if not docs.get('solution_approach'):
            violations.append("missing_solution_documentation")
        if not docs.get('historical_review'):
            violations.append("missing_review_documentation")
        if issue_data['current_state'] == 'completed' and not docs.get('resolution'):
            violations.append("missing_resolution_documentation")
        
        return len(violations) == 0, violations
    
    def check_all_issues(self) -> Dict:
        """Check compliance for all tracked issues"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_issues": 0,
            "compliant_issues": 0,
            "violated_issues": 0,
            "compliance_rate": 0.0,
            "issue_details": {}
        }
        
        for issue_id in self.workflow_data['issue_tracking']:
            compliant, violations = self.check_issue_compliance(issue_id)
            results['total_issues'] += 1
            
            if compliant:
                results['compliant_issues'] += 1
                status = "compliant"
            else:
                results['violated_issues'] += 1
                status = "violated"
            
            results['issue_details'][issue_id] = {
                "status": status,
                "violations": violations,
                "current_state": self.workflow_data['issue_tracking'][issue_id]['current_state']
            }
        
        if results['total_issues'] > 0:
            results['compliance_rate'] = (results['compliant_issues'] / results['total_issues']) * 100
        
        return results
    
    def get_next_allowed_state(self, issue_id: str) -> List[str]:
        """Get the next allowed states for an issue"""
        if issue_id not in self.workflow_data['issue_tracking']:
            return ["issue_discovered"]
        
        current_state = self.workflow_data['issue_tracking'][issue_id]['current_state']
        transitions = self.workflow_data['workflow_states']['transitions']
        
        return transitions.get(current_state, [])
    
    def validate_state_transition(self, issue_id: str, new_state: str) -> Tuple[bool, str]:
        """Validate if a state transition is allowed"""
        allowed_states = self.get_next_allowed_state(issue_id)
        
        if new_state in allowed_states:
            return True, "Transition allowed"
        else:
            return False, f"Invalid transition. Current state allows: {allowed_states}"
    
    def generate_compliance_report(self) -> str:
        """Generate a human-readable compliance report"""
        results = self.check_all_issues()
        
        report = f"""
# Workflow Compliance Report
Generated: {results['timestamp']}

## Summary
- Total Issues: {results['total_issues']}
- Compliant: {results['compliant_issues']} 
- Violations: {results['violated_issues']}
- Compliance Rate: {results['compliance_rate']:.1f}%

## Issue Details
"""
        
        for issue_id, details in results['issue_details'].items():
            report += f"\n### {issue_id}"
            report += f"\n- Status: {details['status'].upper()}"
            report += f"\n- Current State: {details['current_state']}"
            if details['violations']:
                report += f"\n- Violations: {', '.join(details['violations'])}"
            report += "\n"
        
        return report
    
    def get_recovery_plan(self, issue_id: str) -> List[str]:
        """Generate a recovery plan for non-compliant issues"""
        if issue_id not in self.workflow_data['issue_tracking']:
            return ["Issue not found"]
        
        issue_data = self.workflow_data['issue_tracking'][issue_id]
        current_state = issue_data['current_state']
        states_visited = [entry['state'] for entry in issue_data['state_history']]
        
        recovery_steps = []
        
        # Check what's missing
        if 'historical_review' not in states_visited:
            recovery_steps.append("1. Conduct historical review of the solution")
            recovery_steps.append("2. Document findings in historical-review.md")
            recovery_steps.append("3. Get approval before proceeding")
        
        if 'solution_design' not in states_visited:
            recovery_steps.append("1. Document the solution approach")
            recovery_steps.append("2. Update solution-approach.md")
        
        if current_state == 'implementation' and 'approved' not in states_visited:
            recovery_steps.append("1. Stop implementation immediately")
            recovery_steps.append("2. Complete historical review")
            recovery_steps.append("3. Get approval before continuing")
        
        if not issue_data['documentation'].get('resolution') and current_state in ['verification', 'completed']:
            recovery_steps.append("1. Document the resolution in resolution.md")
            recovery_steps.append("2. Include all code changes and verification steps")
        
        return recovery_steps


# CLI Interface
if __name__ == "__main__":
    import sys
    
    checker = ComplianceChecker("workflow-tracking-system.json")
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check-all":
            report = checker.generate_compliance_report()
            print(report)
            
        elif command == "check-issue" and len(sys.argv) > 2:
            issue_id = sys.argv[2]
            compliant, violations = checker.check_issue_compliance(issue_id)
            print(f"{issue_id}: {'COMPLIANT' if compliant else 'VIOLATED'}")
            if violations:
                print(f"Violations: {', '.join(violations)}")
                
        elif command == "next-state" and len(sys.argv) > 2:
            issue_id = sys.argv[2]
            states = checker.get_next_allowed_state(issue_id)
            print(f"Next allowed states for {issue_id}: {states}")
            
        elif command == "recovery-plan" and len(sys.argv) > 2:
            issue_id = sys.argv[2]
            steps = checker.get_recovery_plan(issue_id)
            print(f"\nRecovery plan for {issue_id}:")
            for step in steps:
                print(step)
    else:
        print("Usage:")
        print("  python compliance-checking-system.py check-all")
        print("  python compliance-checking-system.py check-issue DISC-001")
        print("  python compliance-checking-system.py next-state DISC-001")
        print("  python compliance-checking-system.py recovery-plan DISC-002")