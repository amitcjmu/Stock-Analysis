"""
GapAnalyzer assessment readiness determination.

Part of Issue #980: Intelligent Multi-Layer Gap Detection System
"""

import logging
from typing import Any, List

logger = logging.getLogger(__name__)


class ReadinessMixin:
    """Mixin for assessment readiness determination."""

    def _determine_readiness(
        self,
        overall_completeness: float,
        threshold: float,
        critical_gaps: List[str],
        standards_gaps: Any,
    ) -> tuple[bool, List[str]]:
        """
        Determine if asset is ready for assessment.

        Asset is ready if ALL of the following are true:
        1. overall_completeness >= threshold
        2. No critical gaps (priority 1 fields)
        3. No mandatory standards violations

        Args:
            overall_completeness: Weighted completeness score [0.0-1.0]
            threshold: Minimum completeness threshold from requirements
            critical_gaps: List of critical (priority 1) missing fields
            standards_gaps: StandardsGapReport with violations

        Returns:
            Tuple of (is_ready, readiness_blockers)
            - is_ready: bool indicating assessment readiness
            - readiness_blockers: List of reasons why not ready (empty if ready)

        Note:
            Readiness blockers are specific and actionable messages for users.
        """
        blockers = []

        # Check completeness threshold
        if overall_completeness < threshold:
            blockers.append(
                f"Completeness {overall_completeness:.1%} below threshold {threshold:.1%}"
            )

        # Check critical gaps
        if critical_gaps:
            blockers.append(f"Missing {len(critical_gaps)} critical attributes")
            # Add specific critical fields (limit to 5 for readability)
            if len(critical_gaps) <= 5:
                blockers.extend([f"  - {gap}" for gap in critical_gaps])
            else:
                blockers.extend([f"  - {gap}" for gap in critical_gaps[:5]])
                blockers.append(f"  ... and {len(critical_gaps) - 5} more")

        # Check mandatory standards violations
        if standards_gaps.override_required:
            mandatory_violations = [
                v.standard_name
                for v in standards_gaps.violated_standards
                if v.is_mandatory
            ]
            if mandatory_violations:
                blockers.append(
                    f"Violates {len(mandatory_violations)} mandatory standards"
                )
                # Add specific standards (limit to 3)
                for standard in mandatory_violations[:3]:
                    blockers.append(f"  - {standard}")

        is_ready = len(blockers) == 0

        logger.debug(
            "Determined assessment readiness",
            extra={
                "is_ready": is_ready,
                "blocker_count": len(blockers),
                "overall_completeness": overall_completeness,
                "threshold": threshold,
                "critical_gaps_count": len(critical_gaps),
            },
        )

        return is_ready, blockers
