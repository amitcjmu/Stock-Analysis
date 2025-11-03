"""Performance and utilization field definitions for the Asset model."""

from sqlalchemy import Column, Float


class PerformanceFieldsMixin:
    """Mixin providing performance and utilization fields for the Asset model."""

    # Performance and utilization (from Azure Migrate)
    cpu_utilization_percent = Column(
        Float, comment="The average CPU utilization percentage."
    )
    memory_utilization_percent = Column(
        Float, comment="The average memory utilization percentage."
    )
    disk_iops = Column(
        Float, comment="The average disk Input/Output Operations Per Second."
    )
    network_throughput_mbps = Column(
        Float, comment="The average network throughput in megabits per second."
    )

    # Data quality metrics
    completeness_score = Column(
        Float, comment="A score indicating how complete the asset's data is."
    )
    quality_score = Column(
        Float, comment="An overall data quality score for the asset record."
    )
    confidence_score = Column(
        Float,
        comment="A confidence level score for the assessment or data associated with the asset.",
    )

    # Cost metrics
    current_monthly_cost = Column(
        Float, comment="The current monthly operational cost of the asset."
    )
    estimated_cloud_cost = Column(
        Float,
        comment="The estimated cost of running this asset in the cloud after migration.",
    )
