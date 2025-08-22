"""
Bulk Template Service

Handles template generation, management, and export functionality.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from .bulk_data_models import BulkTemplate

logger = logging.getLogger(__name__)


class BulkTemplateService:
    """Manages bulk data templates."""

    def __init__(self):
        """Initialize template service."""
        self.default_templates = self._initialize_default_templates()

    async def generate_bulk_template(
        self,
        template_type: str,
        questionnaire_data: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> BulkTemplate:
        """Generate a bulk data template based on questionnaire data"""
        logger.info(f"Generating bulk template for type: {template_type}")

        # Extract attributes from questionnaire data
        attributes = []
        for question in questionnaire_data:
            if question.get("supports_bulk_entry", False):
                attributes.append(
                    {
                        "name": question["field_name"],
                        "label": question.get("label", question["field_name"]),
                        "data_type": question.get("data_type", "string"),
                        "required": question.get("required", False),
                        "description": question.get("description", ""),
                        "validation_rules": question.get("validation_rules", {}),
                    }
                )

        # Generate validation rules
        validation_rules = {}
        for attr in attributes:
            if attr["validation_rules"]:
                validation_rules[attr["name"]] = attr["validation_rules"]

        # Generate example data
        example_data = self._generate_example_data(attributes, context)

        template = BulkTemplate(
            template_id=str(uuid4()),
            name=f"{template_type.title()} Bulk Entry Template",
            description=f"Template for bulk entry of {template_type} data",
            attributes=attributes,
            validation_rules=validation_rules,
            example_data=example_data,
            created_at=datetime.utcnow(),
        )

        return template

    async def export_template_csv(self, template: BulkTemplate) -> str:
        """Export template as CSV format"""
        import csv
        import io

        output = io.StringIO()
        if not template.attributes:
            return ""

        # Write header
        fieldnames = [attr["name"] for attr in template.attributes]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Write example data if available
        if template.example_data:
            for row in template.example_data[:3]:  # Limit to 3 examples
                writer.writerow(row)

        return output.getvalue()

    async def get_template(self, template_id: str) -> BulkTemplate:
        """Get template by ID"""
        # Try default templates first
        for template in self.default_templates:
            if template.template_id == template_id:
                return template

        # In a real implementation, this would query the database
        raise ValueError(f"Template not found: {template_id}")

    def get_attribute_label(self, attribute_name: str) -> str:
        """Get human-readable label for an attribute"""
        label_map = {
            "name": "Name",
            "description": "Description",
            "ip_address": "IP Address",
            "hostname": "Hostname",
            "operating_system": "Operating System",
            "cpu_cores": "CPU Cores",
            "memory_gb": "Memory (GB)",
            "storage_gb": "Storage (GB)",
            "environment": "Environment",
            "owner": "Owner",
            "cost_center": "Cost Center",
            "application": "Application",
            "service_tier": "Service Tier",
            "backup_required": "Backup Required",
            "monitoring_enabled": "Monitoring Enabled",
        }

        return label_map.get(attribute_name, attribute_name.replace("_", " ").title())

    def _initialize_default_templates(self) -> List[BulkTemplate]:
        """Initialize default templates"""
        return [
            BulkTemplate(
                template_id="server_bulk_template",
                name="Server Infrastructure Bulk Entry",
                description="Template for bulk entry of server infrastructure data",
                attributes=[
                    {
                        "name": "name",
                        "label": "Server Name",
                        "data_type": "string",
                        "required": True,
                        "description": "Unique server identifier",
                    },
                    {
                        "name": "ip_address",
                        "label": "IP Address",
                        "data_type": "string",
                        "required": True,
                        "description": "Primary IP address",
                    },
                    {
                        "name": "operating_system",
                        "label": "Operating System",
                        "data_type": "string",
                        "required": True,
                        "description": "OS name and version",
                    },
                    {
                        "name": "cpu_cores",
                        "label": "CPU Cores",
                        "data_type": "integer",
                        "required": False,
                        "description": "Number of CPU cores",
                    },
                    {
                        "name": "memory_gb",
                        "label": "Memory (GB)",
                        "data_type": "float",
                        "required": False,
                        "description": "Total memory in GB",
                    },
                    {
                        "name": "environment",
                        "label": "Environment",
                        "data_type": "string",
                        "required": True,
                        "description": "Environment type",
                    },
                ],
                validation_rules={
                    "name": {"pattern": r"^[a-zA-Z0-9\-]+$"},
                    "ip_address": {
                        "pattern": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
                        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
                    },
                    "cpu_cores": {"min_value": 1, "max_value": 256},
                    "memory_gb": {"min_value": 0.1, "max_value": 4096},
                    "environment": {
                        "allowed_values": [
                            "development",
                            "staging",
                            "production",
                            "test",
                        ]
                    },
                },
                example_data=[
                    {
                        "name": "web-server-01",
                        "ip_address": "192.168.1.10",
                        "operating_system": "Ubuntu 20.04 LTS",
                        "cpu_cores": 4,
                        "memory_gb": 16.0,
                        "environment": "production",
                    },
                    {
                        "name": "db-server-01",
                        "ip_address": "192.168.1.20",
                        "operating_system": "CentOS 8",
                        "cpu_cores": 8,
                        "memory_gb": 32.0,
                        "environment": "production",
                    },
                ],
                created_at=datetime.utcnow(),
            )
        ]

    def _generate_example_data(
        self, attributes: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate example data for template"""
        examples = []

        # Generate 2-3 example rows
        for i in range(min(3, len(attributes))):
            example_row = {}
            for attr in attributes:
                example_row[attr["name"]] = self._generate_example_value(
                    attr, context, i
                )
            examples.append(example_row)

        return examples

    def _generate_example_value(
        self, attribute: Dict[str, Any], context: Dict[str, Any], index: int
    ) -> Any:
        """Generate example value for an attribute"""
        attr_name = attribute["name"].lower()
        data_type = attribute.get("data_type", "string")

        # Generate based on attribute name patterns
        if "name" in attr_name:
            return f"example-{attr_name.replace('_', '-')}-{index + 1:02d}"
        elif "ip" in attr_name:
            return f"192.168.1.{10 + index}"
        elif "email" in attr_name:
            return f"user{index + 1}@example.com"
        elif "url" in attr_name:
            return f"https://example-{index + 1}.com"
        elif "port" in attr_name:
            return 8080 + index
        elif "environment" in attr_name:
            envs = ["development", "staging", "production"]
            return envs[index % len(envs)]
        elif "os" in attr_name or "operating_system" in attr_name:
            oses = ["Ubuntu 20.04 LTS", "CentOS 8", "Windows Server 2019"]
            return oses[index % len(oses)]
        elif data_type == "integer":
            return (index + 1) * 2
        elif data_type == "float":
            return round((index + 1) * 1.5, 1)
        elif data_type == "boolean":
            return index % 2 == 0
        else:
            return f"example-value-{index + 1}"
