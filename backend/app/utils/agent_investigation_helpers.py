"""
Agent Investigation Helpers - Anti-Hallucination Utilities

This module provides helper functions for agents to properly investigate
issues without hallucinating solutions.
"""

import json
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence levels for hypotheses."""

    HIGH = "HIGH"  # 90-100% - Strong evidence
    MEDIUM = "MEDIUM"  # 70-89% - Good evidence
    LOW = "LOW"  # <70% - Insufficient evidence


class EvidenceSource(Enum):
    """Types of evidence sources."""

    BACKEND_LOGS = "backend_logs"
    FRONTEND_LOGS = "frontend_logs"
    BROWSER_CONSOLE = "browser_console"
    NETWORK_REQUESTS = "network_requests"
    DATABASE_STATE = "database_state"
    CODE_REVIEW = "code_review"
    GIT_HISTORY = "git_history"


@dataclass
class Evidence:
    """Evidence collected during investigation."""

    source: EvidenceSource
    content: str
    timestamp: datetime
    relevance_score: float  # 0-1, how relevant to the issue

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source": self.source.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "relevance_score": self.relevance_score,
        }


@dataclass
class Hypothesis:
    """A hypothesis about the root cause."""

    description: str
    confidence: ConfidenceLevel
    confidence_score: float  # 0-100
    supporting_evidence: List[Evidence]
    contradicting_evidence: List[Evidence]
    test_method: str
    test_result: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "description": self.description,
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "supporting_evidence": [e.to_dict() for e in self.supporting_evidence],
            "contradicting_evidence": [
                e.to_dict() for e in self.contradicting_evidence
            ],
            "test_method": self.test_method,
            "test_result": self.test_result,
        }


@dataclass
class InvestigationResult:
    """Complete investigation result."""

    issue_description: str
    evidence_collected: List[Evidence]
    hypotheses: List[Hypothesis]
    root_cause: Optional[str]
    proposed_solution: Optional[str]
    confidence_in_solution: Optional[ConfidenceLevel]
    requires_user_input: bool
    questions_for_user: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "issue_description": self.issue_description,
            "evidence_collected": [e.to_dict() for e in self.evidence_collected],
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "root_cause": self.root_cause,
            "proposed_solution": self.proposed_solution,
            "confidence_in_solution": (
                self.confidence_in_solution.value
                if self.confidence_in_solution
                else None
            ),
            "requires_user_input": self.requires_user_input,
            "questions_for_user": self.questions_for_user,
            "timestamp": datetime.now().isoformat(),
        }


class AgentInvestigator:
    """Helper class for agents to investigate issues properly."""

    def __init__(self, agent_name: str):
        """Initialize the investigator."""
        self.agent_name = agent_name
        self.evidence: List[Evidence] = []
        self.hypotheses: List[Hypothesis] = []

    def collect_backend_logs(
        self, tail_lines: int = 100, grep_pattern: Optional[str] = None
    ) -> Evidence:
        """Collect backend logs as evidence."""
        try:
            cmd = f"docker logs migration_backend --tail {tail_lines}"
            if grep_pattern:
                cmd += f" 2>&1 | grep -i '{grep_pattern}'"

            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True
            )  # nosec B602
            content = result.stdout or result.stderr or "No logs found"

            evidence = Evidence(
                source=EvidenceSource.BACKEND_LOGS,
                content=content[:5000],  # Limit size
                timestamp=datetime.now(),
                relevance_score=0.9 if grep_pattern and content else 0.5,
            )
            self.evidence.append(evidence)
            return evidence

        except Exception as e:
            logger.error(f"Failed to collect backend logs: {e}")
            evidence = Evidence(
                source=EvidenceSource.BACKEND_LOGS,
                content=f"Error collecting logs: {str(e)}",
                timestamp=datetime.now(),
                relevance_score=0.1,
            )
            self.evidence.append(evidence)
            return evidence

    def collect_frontend_logs(self, tail_lines: int = 50) -> Evidence:
        """Collect frontend logs as evidence."""
        try:
            cmd = f"docker logs migration_frontend --tail {tail_lines}"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True
            )  # nosec B602
            content = result.stdout or result.stderr or "No logs found"

            evidence = Evidence(
                source=EvidenceSource.FRONTEND_LOGS,
                content=content[:3000],
                timestamp=datetime.now(),
                relevance_score=0.7,
            )
            self.evidence.append(evidence)
            return evidence

        except Exception as e:
            logger.error(f"Failed to collect frontend logs: {e}")
            evidence = Evidence(
                source=EvidenceSource.FRONTEND_LOGS,
                content=f"Error collecting logs: {str(e)}",
                timestamp=datetime.now(),
                relevance_score=0.1,
            )
            self.evidence.append(evidence)
            return evidence

    def collect_git_history(self, num_commits: int = 10) -> Evidence:
        """Collect recent git history as evidence."""
        try:
            cmd = f"git log --oneline -{num_commits}"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True
            )  # nosec B602
            content = result.stdout or "No git history found"

            evidence = Evidence(
                source=EvidenceSource.GIT_HISTORY,
                content=content,
                timestamp=datetime.now(),
                relevance_score=0.6,
            )
            self.evidence.append(evidence)
            return evidence

        except Exception as e:
            logger.error(f"Failed to collect git history: {e}")
            evidence = Evidence(
                source=EvidenceSource.GIT_HISTORY,
                content=f"Error collecting git history: {str(e)}",
                timestamp=datetime.now(),
                relevance_score=0.1,
            )
            self.evidence.append(evidence)
            return evidence

    def add_manual_evidence(
        self, source: EvidenceSource, content: str, relevance_score: float = 0.5
    ) -> Evidence:
        """Add manually collected evidence (e.g., browser console, network tab)."""
        evidence = Evidence(
            source=source,
            content=content,
            timestamp=datetime.now(),
            relevance_score=relevance_score,
        )
        self.evidence.append(evidence)
        return evidence

    def form_hypothesis(
        self,
        description: str,
        confidence_score: float,
        supporting_evidence: List[Evidence],
        test_method: str,
        contradicting_evidence: Optional[List[Evidence]] = None,
    ) -> Hypothesis:
        """Form a hypothesis about the root cause."""
        # Determine confidence level
        if confidence_score >= 90:
            confidence = ConfidenceLevel.HIGH
        elif confidence_score >= 70:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW

        hypothesis = Hypothesis(
            description=description,
            confidence=confidence,
            confidence_score=confidence_score,
            supporting_evidence=supporting_evidence,
            contradicting_evidence=contradicting_evidence or [],
            test_method=test_method,
        )
        self.hypotheses.append(hypothesis)
        return hypothesis

    def test_hypothesis(self, hypothesis: Hypothesis, test_result: str) -> None:
        """Record the result of testing a hypothesis."""
        hypothesis.test_result = test_result

        # Adjust confidence based on test result
        if "confirmed" in test_result.lower() or "success" in test_result.lower():
            hypothesis.confidence_score = min(100, hypothesis.confidence_score + 10)
        elif "failed" in test_result.lower() or "rejected" in test_result.lower():
            hypothesis.confidence_score = max(0, hypothesis.confidence_score - 30)

        # Update confidence level
        if hypothesis.confidence_score >= 90:
            hypothesis.confidence = ConfidenceLevel.HIGH
        elif hypothesis.confidence_score >= 70:
            hypothesis.confidence = ConfidenceLevel.MEDIUM
        else:
            hypothesis.confidence = ConfidenceLevel.LOW

    def determine_root_cause(self) -> Tuple[Optional[str], ConfidenceLevel]:
        """Determine the most likely root cause based on evidence and testing."""
        if not self.hypotheses:
            return None, ConfidenceLevel.LOW

        # Sort hypotheses by confidence score
        sorted_hypotheses = sorted(
            self.hypotheses, key=lambda h: h.confidence_score, reverse=True
        )

        best_hypothesis = sorted_hypotheses[0]

        # Only return root cause if confidence is sufficient
        if best_hypothesis.confidence_score >= 80:
            return best_hypothesis.description, best_hypothesis.confidence
        else:
            return None, ConfidenceLevel.LOW

    def generate_investigation_report(
        self, issue_description: str, proposed_solution: Optional[str] = None
    ) -> InvestigationResult:
        """Generate a complete investigation report."""
        root_cause, confidence = self.determine_root_cause()

        # Determine if user input is needed
        requires_user_input = (
            confidence == ConfidenceLevel.LOW
            or root_cause is None
            or len(self.evidence) < 3
        )

        # Generate questions for user if needed
        questions = []
        if requires_user_input:
            if len(self.evidence) < 3:
                questions.append("Can you provide browser console errors?")
                questions.append("What exact steps reproduce the issue?")
            if confidence == ConfidenceLevel.LOW:
                questions.append("Can you check the network tab for failed requests?")
                questions.append("Were there any recent changes to this functionality?")

        return InvestigationResult(
            issue_description=issue_description,
            evidence_collected=self.evidence,
            hypotheses=self.hypotheses,
            root_cause=root_cause,
            proposed_solution=(
                proposed_solution if confidence != ConfidenceLevel.LOW else None
            ),
            confidence_in_solution=confidence if proposed_solution else None,
            requires_user_input=requires_user_input,
            questions_for_user=questions,
        )

    def save_audit_log(self, result: InvestigationResult) -> None:
        """Save investigation to audit log."""
        try:
            log_file = "/.claude/agent_audit.log"
            with open(log_file, "a") as f:
                log_entry = {
                    "agent": self.agent_name,
                    "investigation": result.to_dict(),
                }
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")


def format_investigation_for_user(result: InvestigationResult) -> str:
    """Format investigation result for user presentation."""
    output = []
    output.append("## Investigation Results\n")

    # Evidence summary
    output.append("### Evidence Collected:")
    evidence_by_source = {}
    for e in result.evidence_collected:
        if e.source not in evidence_by_source:
            evidence_by_source[e.source] = []
        evidence_by_source[e.source].append(e)

    for source, evidences in evidence_by_source.items():
        output.append(f"- ✅ {source.value}: {len(evidences)} items collected")

    # Hypotheses
    output.append("\n### Hypotheses Tested:")
    for i, h in enumerate(result.hypotheses, 1):
        output.append(
            f"{i}. **{h.description}** (Confidence: {h.confidence_score:.0f}%)"
        )
        if h.test_result:
            output.append(f"   - Test result: {h.test_result}")

    # Root cause
    if result.root_cause:
        output.append(f"\n### Root Cause:\n{result.root_cause}")
        output.append(f"Confidence: {result.confidence_in_solution.value}")
    else:
        output.append(
            "\n### Root Cause:\nInsufficient evidence to determine root cause"
        )

    # Solution
    if result.proposed_solution:
        output.append(f"\n### Proposed Solution:\n{result.proposed_solution}")

    # User input needed
    if result.requires_user_input:
        output.append("\n### ⚠️ Additional Information Needed:")
        for q in result.questions_for_user:
            output.append(f"- {q}")

    return "\n".join(output)


# Example usage for agents
def investigate_issue_example(issue_description: str) -> str:
    """
    Example of how agents should investigate issues.

    This follows the anti-hallucination protocol.
    """
    investigator = AgentInvestigator("example-agent")

    # Step 1: Collect evidence
    investigator.collect_backend_logs(grep_pattern="error")
    investigator.collect_frontend_logs()
    investigator.collect_git_history()

    # Step 2: Form hypotheses based on evidence
    if "AuthenticationError" in investigator.evidence[0].content:
        investigator.form_hypothesis(
            description="Authentication token expired or invalid",
            confidence_score=85,
            supporting_evidence=[investigator.evidence[0]],
            test_method="Check if fresh token works",
        )

    # Step 3: Test hypotheses (in real scenario, actually test)
    if investigator.hypotheses:
        investigator.test_hypothesis(
            investigator.hypotheses[0], "Tested with fresh token - issue persists"
        )

    # Step 4: Generate report
    result = investigator.generate_investigation_report(
        issue_description=issue_description,
        proposed_solution="Refresh authentication token and retry",
    )

    # Step 5: Save audit log
    investigator.save_audit_log(result)

    # Return formatted report for user
    return format_investigation_for_user(result)
