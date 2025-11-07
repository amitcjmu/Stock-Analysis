"""
End-of-Life (EOL) detection utilities for collection questionnaires.
Functions for determining EOL status of operating systems and technologies.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

# Known EOL operating systems and versions
EOL_OS_PATTERNS = {
    "AIX 7.1": "EOL_EXPIRED",
    "AIX 7.2": "EOL_EXPIRED",  # IBM ended extended support
    "Windows Server 2008": "EOL_EXPIRED",
    "Windows Server 2012": "EOL_EXPIRED",
    "RHEL 6": "EOL_EXPIRED",
    "RHEL 7": "EOL_SOON",
    "Solaris 10": "EOL_EXPIRED",
}

# Known EOL technology stack components
EOL_TECH_PATTERNS = {
    "websphere_85": "EOL_EXPIRED",  # WebSphere 8.5.x extended support ended
    "websphere_9": "EOL_SOON",
    "jboss_6": "EOL_EXPIRED",
    "tomcat_7": "EOL_EXPIRED",
}


def _determine_eol_status(
    operating_system: str, os_version: str, technology_stack: List[str]
) -> str:
    """
    Determine EOL technology status based on OS and technology stack.

    Returns:
        EOL status string: "EOL_EXPIRED", "EOL_SOON", "DEPRECATED", or "CURRENT"
    """
    # Check OS
    if operating_system and os_version:
        os_key = f"{operating_system} {os_version}".strip()
        for pattern, status in EOL_OS_PATTERNS.items():
            if pattern in os_key:
                logger.info(f"Detected EOL OS: {os_key} → {status}")
                return status

    # Check technology stack
    if technology_stack and isinstance(technology_stack, list):
        for tech in technology_stack:
            if tech in EOL_TECH_PATTERNS:
                logger.info(
                    f"Detected EOL technology: {tech} → {EOL_TECH_PATTERNS[tech]}"
                )
                return EOL_TECH_PATTERNS[tech]

    # Default to CURRENT if no EOL indicators found
    return "CURRENT"
