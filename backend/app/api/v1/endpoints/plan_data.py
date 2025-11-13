"""
Mock data for Plan API endpoints.

TODO: Replace with real database queries when resource_teams table is created.
"""

from datetime import datetime, timedelta
from typing import Any, Dict


def get_resource_mock_data(current_date: datetime) -> Dict[str, Any]:
    """Generate resource planning mock data with teams, metrics, and recommendations."""
    return {
        "teams": [
            {
                "id": "team-1",
                "name": "Cloud Infrastructure Team",
                "size": 8,
                "skills": ["AWS", "Azure", "Terraform", "Kubernetes"],
                "availability": 85,
                "utilization": 78,
                "assignments": [
                    {
                        "project": "Wave 1 Migration",
                        "allocation": 60,
                        "start_date": current_date.strftime("%Y-%m-%d"),
                        "end_date": (current_date + timedelta(days=90)).strftime(
                            "%Y-%m-%d"
                        ),
                    },
                    {
                        "project": "Infrastructure Assessment",
                        "allocation": 18,
                        "start_date": current_date.strftime("%Y-%m-%d"),
                        "end_date": (current_date + timedelta(days=30)).strftime(
                            "%Y-%m-%d"
                        ),
                    },
                ],
            },
            {
                "id": "team-2",
                "name": "Application Migration Team",
                "size": 12,
                "skills": ["Java", "Python", ".NET", "Containerization"],
                "availability": 92,
                "utilization": 85,
                "assignments": [
                    {
                        "project": "Wave 1 Migration",
                        "allocation": 70,
                        "start_date": (current_date + timedelta(days=30)).strftime(
                            "%Y-%m-%d"
                        ),
                        "end_date": (current_date + timedelta(days=120)).strftime(
                            "%Y-%m-%d"
                        ),
                    },
                    {
                        "project": "Modernization Prep",
                        "allocation": 15,
                        "start_date": current_date.strftime("%Y-%m-%d"),
                        "end_date": (current_date + timedelta(days=45)).strftime(
                            "%Y-%m-%d"
                        ),
                    },
                ],
            },
            {
                "id": "team-3",
                "name": "Data Migration Team",
                "size": 6,
                "skills": ["SQL", "ETL", "Data Modeling", "PostgreSQL"],
                "availability": 75,
                "utilization": 92,
                "assignments": [
                    {
                        "project": "Database Migration Wave 1",
                        "allocation": 80,
                        "start_date": (current_date + timedelta(days=15)).strftime(
                            "%Y-%m-%d"
                        ),
                        "end_date": (current_date + timedelta(days=75)).strftime(
                            "%Y-%m-%d"
                        ),
                    },
                    {
                        "project": "Data Quality Assessment",
                        "allocation": 12,
                        "start_date": current_date.strftime("%Y-%m-%d"),
                        "end_date": (current_date + timedelta(days=30)).strftime(
                            "%Y-%m-%d"
                        ),
                    },
                ],
            },
            {
                "id": "team-4",
                "name": "Testing & QA Team",
                "size": 10,
                "skills": [
                    "Automated Testing",
                    "Performance Testing",
                    "Security Testing",
                ],
                "availability": 88,
                "utilization": 65,
                "assignments": [
                    {
                        "project": "Wave 1 Testing",
                        "allocation": 50,
                        "start_date": (current_date + timedelta(days=45)).strftime(
                            "%Y-%m-%d"
                        ),
                        "end_date": (current_date + timedelta(days=105)).strftime(
                            "%Y-%m-%d"
                        ),
                    },
                    {
                        "project": "Test Automation Setup",
                        "allocation": 15,
                        "start_date": current_date.strftime("%Y-%m-%d"),
                        "end_date": (current_date + timedelta(days=60)).strftime(
                            "%Y-%m-%d"
                        ),
                    },
                ],
            },
        ],
        "metrics": {
            "total_teams": 4,
            "total_resources": 36,
            "average_utilization": 80,
            "skill_coverage": {
                "Cloud Infrastructure": 95,
                "Application Development": 88,
                "Data Engineering": 82,
                "Testing & QA": 90,
                "Security": 75,
                "DevOps": 85,
            },
        },
        "recommendations": [
            {
                "type": "capacity",
                "description": (
                    "Data Migration Team is at 92% utilization. "
                    "Consider adding 2 resources to prevent burnout."
                ),
                "impact": "High",
            },
            {
                "type": "skills",
                "description": (
                    "Security expertise is at 75% coverage. "
                    "Recommend cross-training or hiring for upcoming "
                    "compliance work."
                ),
                "impact": "Medium",
            },
            {
                "type": "optimization",
                "description": (
                    "Testing Team has available capacity. "
                    "Can be allocated to automation framework development."
                ),
                "impact": "Low",
            },
            {
                "type": "planning",
                "description": (
                    "Wave 2 migration starts in 45 days. "
                    "Begin resource allocation planning now to "
                    "avoid conflicts."
                ),
                "impact": "Medium",
            },
        ],
        "upcoming_needs": [
            {
                "skill": "Kubernetes Migration",
                "demand": 4,
                "timeline": (current_date + timedelta(days=60)).strftime("%Y-%m-%d"),
            },
            {
                "skill": "Serverless Architecture",
                "demand": 3,
                "timeline": (current_date + timedelta(days=90)).strftime("%Y-%m-%d"),
            },
            {
                "skill": "Security Compliance",
                "demand": 2,
                "timeline": (current_date + timedelta(days=30)).strftime("%Y-%m-%d"),
            },
        ],
    }
