"""Performance and utilization field definitions for the Asset model."""

from sqlalchemy import Column, Float


class PerformanceFieldsMixin:
    """Mixin providing performance and utilization fields for the Asset model."""

    # Performance and utilization (from Azure Migrate)
    cpu_utilization_percent = Column(
        Float,
        comment="The average CPU utilization percentage.",
        info={
            "display_name": "CPU Utilization (Avg %)",
            "short_hint": "0-100%",
            "category": "performance",
        },
    )
    memory_utilization_percent = Column(
        Float,
        comment="The average memory utilization percentage.",
        info={
            "display_name": "Memory Utilization (Avg %)",
            "short_hint": "0-100%",
            "category": "performance",
        },
    )
    disk_iops = Column(
        Float,
        comment="The average disk Input/Output Operations Per Second.",
        info={
            "display_name": "Disk IOPS",
            "short_hint": "I/O operations per second",
            "category": "performance",
        },
    )
    network_throughput_mbps = Column(
        Float,
        comment="The average network throughput in megabits per second.",
        info={
            "display_name": "Network Throughput (Mbps)",
            "short_hint": "Megabits per second",
            "category": "performance",
        },
    )

    # Data quality metrics
    completeness_score = Column(
        Float,
        comment="A score indicating how complete the asset's data is.",
        info={
            "display_name": "Data Completeness Score",
            "short_hint": "0-100 scale",
            "category": "assessment",
        },
    )
    quality_score = Column(
        Float,
        comment="An overall data quality score for the asset record.",
        info={
            "display_name": "Data Quality Score",
            "short_hint": "0-100 scale",
            "category": "assessment",
        },
    )
    confidence_score = Column(
        Float,
        comment="A confidence level score for the assessment or data associated with the asset.",
        info={
            "display_name": "Confidence Score",
            "short_hint": "0-100 scale",
            "category": "assessment",
        },
    )

    # Cost metrics
    current_monthly_cost = Column(
        Float,
        comment="The current monthly operational cost of the asset.",
        info={
            "display_name": "Current Monthly Cost",
            "short_hint": "Current monthly cost in USD",
            "category": "business",
        },
    )
    estimated_cloud_cost = Column(
        Float,
        comment="The estimated cost of running this asset in the cloud after migration.",
        info={
            "display_name": "Estimated Cloud Cost",
            "short_hint": "Projected monthly cloud cost",
            "category": "migration",
        },
    )
