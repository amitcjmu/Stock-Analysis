"""Performance and utilization field definitions for the Asset model."""

from sqlalchemy import Column, Float


class PerformanceFieldsMixin:
    """Mixin providing performance and utilization fields for the Asset model."""

    # Performance and utilization (from Azure Migrate)
    cpu_utilization_percent = Column(
        Float,
        comment="The average CPU utilization percentage.",
        info={
            "display_name": "CPU Utilization %",
            "short_hint": "Average CPU usage",
            "category": "performance",
        },
    )
    memory_utilization_percent = Column(
        Float,
        comment="The average memory utilization percentage.",
        info={
            "display_name": "Memory Utilization %",
            "short_hint": "Average memory usage",
            "category": "performance",
        },
    )
    disk_iops = Column(
        Float,
        comment="The average disk Input/Output Operations Per Second.",
        info={
            "display_name": "Disk IOPS",
            "short_hint": "Disk I/O operations/sec",
            "category": "performance",
        },
    )
    network_throughput_mbps = Column(
        Float,
        comment="The average network throughput in megabits per second.",
        info={
            "display_name": "Network Throughput (Mbps)",
            "short_hint": "Network speed in Mbps",
            "category": "performance",
        },
    )

    # Data quality metrics
    completeness_score = Column(
        Float,
        comment="A score indicating how complete the asset's data is.",
        info={
            "display_name": "Completeness Score",
            "short_hint": "Data completeness score",
            "category": "assessment",
        },
    )
    quality_score = Column(
        Float,
        comment="An overall data quality score for the asset record.",
        info={
            "display_name": "Quality Score",
            "short_hint": "Data quality score",
            "category": "assessment",
        },
    )
    confidence_score = Column(
        Float,
        comment="A confidence level score for the assessment or data associated with the asset.",
        info={
            "display_name": "Confidence Score",
            "short_hint": "Assessment confidence level",
            "category": "assessment",
        },
    )

    # Cost metrics
    current_monthly_cost = Column(
        Float,
        comment="The current monthly operational cost of the asset.",
        info={
            "display_name": "Current Monthly Cost",
            "short_hint": "Monthly operational cost",
            "category": "business",
        },
    )
    estimated_cloud_cost = Column(
        Float,
        comment="The estimated cost of running this asset in the cloud after migration.",
        info={
            "display_name": "Estimated Cloud Cost",
            "short_hint": "Projected cloud cost",
            "category": "migration",
        },
    )
