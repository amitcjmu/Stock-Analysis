"""
Azure Data Operations Module for ADCS Implementation

This module handles Azure data resource operations including SQL Databases.
Provides detailed resource enhancement and performance metrics collection
for database workloads and data services.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

try:
    from azure.mgmt.monitor import MonitorManagementClient
    from azure.mgmt.sql import SqlManagementClient

    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    MonitorManagementClient = SqlManagementClient = None

logger = logging.getLogger(__name__)


class AzureDataOperations:
    """
    Azure Data Operations for ADCS Implementation

    Handles SQL Database resource enhancement, metrics collection,
    and detailed database information gathering for data asset discovery.
    """

    def __init__(
        self,
        sql_client: SqlManagementClient,
        monitor_client: MonitorManagementClient,
    ):
        """
        Initialize Azure data operations

        Args:
            sql_client: Azure SQL Management client
            monitor_client: Azure Monitor Management client
        """
        self._sql_client = sql_client
        self._monitor_client = monitor_client

    async def enhance_sql_database_data(
        self, db_resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance SQL database data with detailed information

        Args:
            db_resource: Basic SQL database resource data from Resource Graph

        Returns:
            Enhanced SQL database data with detailed database properties
        """
        try:
            # Parse resource ID to get server and database info
            resource_id = db_resource.get("id", "")
            parts = resource_id.split("/")

            if len(parts) >= 11:
                resource_group = parts[4]
                server_name = parts[8]
                database_name = parts[10]

                # Get detailed database information
                database = self._sql_client.databases.get(
                    resource_group_name=resource_group,
                    server_name=server_name,
                    database_name=database_name,
                )

                return {
                    "sku": {
                        "name": database.sku.name if database.sku else None,
                        "tier": database.sku.tier if database.sku else None,
                        "capacity": database.sku.capacity if database.sku else None,
                    },
                    "status": database.status,
                    "creation_date": (
                        database.creation_date.isoformat()
                        if database.creation_date
                        else None
                    ),
                    "collation": database.collation,
                    "max_size_bytes": database.max_size_bytes,
                    "current_backup_storage_redundancy": database.current_backup_storage_redundancy,
                    "zone_redundant": database.zone_redundant,
                    "read_scale": database.read_scale,
                    "elastic_pool_id": database.elastic_pool_id,
                }

        except Exception as e:
            logger.warning(
                f"Failed to enhance SQL database data for {db_resource.get('name')}: {str(e)}"
            )

        return {}

    async def collect_sql_metrics(
        self, databases: List[Dict], start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """
        Collect Azure Monitor metrics for SQL Databases

        Args:
            databases: List of SQL database resource dictionaries
            start_time: Start time for metrics collection
            end_time: End time for metrics collection

        Returns:
            List of SQL database performance metrics
        """
        metrics = []

        for db in databases:
            resource_id = db.get("id")
            if not resource_id:
                continue

            try:
                # Define metrics to collect for SQL databases
                metric_names = [
                    "cpu_percent",
                    "dtu_consumption_percent",
                    "storage_percent",
                    "connection_successful",
                    "connection_failed",
                ]

                db_metrics = {
                    "resource_id": resource_id,
                    "resource_type": "SqlDatabase",
                    "resource_name": db.get("name"),
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Collect each metric
                for metric_name in metric_names:
                    try:
                        metric_data = self._monitor_client.metrics.list(
                            resource_uri=resource_id,
                            timespan=f"{start_time.isoformat()}/{end_time.isoformat()}",
                            interval="PT1H",
                            metricnames=metric_name,
                            aggregation="Average",
                        )

                        if metric_data.value:
                            metric_values = []
                            for metric in metric_data.value:
                                if metric.timeseries:
                                    for timeseries in metric.timeseries:
                                        if timeseries.data:
                                            metric_values.extend(
                                                [
                                                    data.average
                                                    for data in timeseries.data
                                                    if data.average is not None
                                                ]
                                            )

                            if metric_values:
                                avg_value = sum(metric_values) / len(metric_values)
                                db_metrics[metric_name] = avg_value

                    except Exception as e:
                        logger.warning(
                            f"Failed to collect {metric_name} for SQL DB {db.get('name')}: {str(e)}"
                        )

                metrics.append(db_metrics)

            except Exception as e:
                logger.warning(
                    f"Failed to collect metrics for SQL DB {db.get('name')}: {str(e)}"
                )

        return metrics
