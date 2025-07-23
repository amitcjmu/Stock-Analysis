"""
GCP Adapter Constants

Contains constants and configuration values used across the GCP adapter.
"""

# Supported GCP asset types for discovery
SUPPORTED_ASSET_TYPES = {
    "compute.googleapis.com/Instance",
    "sqladmin.googleapis.com/Instance",
    "storage.googleapis.com/Bucket",
    "container.googleapis.com/Cluster",
    "cloudfunctions.googleapis.com/CloudFunction",
    "compute.googleapis.com/ForwardingRule",
    "compute.googleapis.com/UrlMap",
    "compute.googleapis.com/TargetHttpProxy",
    "compute.googleapis.com/TargetHttpsProxy",
    "compute.googleapis.com/BackendService",
    "compute.googleapis.com/Network",
    "compute.googleapis.com/Subnetwork",
    "compute.googleapis.com/Firewall",
    "bigquery.googleapis.com/Dataset",
    "bigquery.googleapis.com/Table",
}

# Target mapping for user-friendly resource names
TARGET_MAPPING = {
    "Instances": "compute.googleapis.com/Instance",
    "VM": "compute.googleapis.com/Instance",
    "Compute": "compute.googleapis.com/Instance",
    "SQL": "sqladmin.googleapis.com/Instance",
    "Databases": "sqladmin.googleapis.com/Instance",
    "Storage": "storage.googleapis.com/Bucket",
    "Buckets": "storage.googleapis.com/Bucket",
    "GKE": "container.googleapis.com/Cluster",
    "Kubernetes": "container.googleapis.com/Cluster",
    "Functions": "cloudfunctions.googleapis.com/CloudFunction",
    "LoadBalancers": "compute.googleapis.com/ForwardingRule",
    "Networks": "compute.googleapis.com/Network",
    "BigQuery": "bigquery.googleapis.com/Dataset",
}

# Asset type to normalized type mapping
ASSET_TYPE_MAP = {
    "compute.googleapis.com/Instance": "server",
    "sqladmin.googleapis.com/Instance": "database",
    "storage.googleapis.com/Bucket": "storage",
    "container.googleapis.com/Cluster": "kubernetes_cluster",
    "cloudfunctions.googleapis.com/CloudFunction": "application",
    "compute.googleapis.com/ForwardingRule": "load_balancer",
    "compute.googleapis.com/UrlMap": "load_balancer",
    "compute.googleapis.com/TargetHttpProxy": "load_balancer",
    "compute.googleapis.com/TargetHttpsProxy": "load_balancer",
    "compute.googleapis.com/BackendService": "load_balancer",
    "compute.googleapis.com/Network": "network",
    "compute.googleapis.com/Subnetwork": "network",
    "compute.googleapis.com/Firewall": "security_group",
    "bigquery.googleapis.com/Dataset": "data_warehouse",
    "bigquery.googleapis.com/Table": "data_warehouse",
}

# Metric types for different GCP services
COMPUTE_METRICS = [
    "compute.googleapis.com/instance/cpu/utilization",
    "compute.googleapis.com/instance/network/received_bytes_count",
    "compute.googleapis.com/instance/network/sent_bytes_count",
    "compute.googleapis.com/instance/disk/read_bytes_count",
    "compute.googleapis.com/instance/disk/write_bytes_count",
]

SQL_METRICS = [
    "cloudsql.googleapis.com/database/cpu/utilization",
    "cloudsql.googleapis.com/database/memory/utilization",
    "cloudsql.googleapis.com/database/disk/utilization",
    "cloudsql.googleapis.com/database/network/received_bytes_count",
    "cloudsql.googleapis.com/database/network/sent_bytes_count",
]

FUNCTION_METRICS = [
    "cloudfunctions.googleapis.com/function/executions",
    "cloudfunctions.googleapis.com/function/execution_times",
    "cloudfunctions.googleapis.com/function/user_memory_bytes",
    "cloudfunctions.googleapis.com/function/network_egress",
]
