"""
Query Builders for Grafana Dashboard Metrics

Provides pre-built Prometheus query configurations for different metric types.
Contains query builders for authentication, cache, system, and performance metrics.
"""

from typing import Any, Dict, List


class MetricQueryBuilder:
    """
    Builder class for Prometheus metric queries

    Provides pre-built query configurations for common monitoring metrics.
    Supports authentication, cache, system health, and performance queries.
    """

    @staticmethod
    def get_auth_performance_queries() -> Dict[str, Dict[str, Any]]:
        """Get authentication performance metric queries"""
        return {
            "login_p95": {
                "expr": 'auth_login_duration_seconds{quantile="0.95"} * 1000',
                "legendFormat": "Login P95 (ms)",
            },
            "login_p50": {
                "expr": "histogram_quantile(0.50, rate(auth_login_duration_seconds_bucket[5m])) * 1000",
                "legendFormat": "P50",
            },
            "login_p99": {
                "expr": "histogram_quantile(0.99, rate(auth_login_duration_seconds_bucket[5m])) * 1000",
                "legendFormat": "P99",
            },
            "session_validation_p95": {
                "expr": 'auth_session_validation_duration_seconds{quantile="0.95"} * 1000',
                "legendFormat": "Session Validation P95 (ms)",
            },
            "context_switch_p95": {
                "expr": 'auth_context_switch_duration_seconds{quantile="0.95"} * 1000',
                "legendFormat": "Context Switch P95 (ms)",
            },
            "success_rate": {
                "expr": (
                    'rate(auth_login_attempts_total{status="success"}[5m]) / '
                    "rate(auth_login_attempts_total[5m]) * 100"
                ),
                "legendFormat": "Login Success Rate",
            },
        }

    @staticmethod
    def get_cache_performance_queries() -> Dict[str, Dict[str, Any]]:
        """Get cache performance metric queries"""
        return {
            "overall_hit_rate": {
                "expr": "cache_hit_ratio",
                "legendFormat": "Overall Cache Hit Rate %",
            },
            "redis_hit_rate": {
                "expr": 'cache_hit_ratio{cache_type="redis"}',
                "legendFormat": "Redis Hit Rate %",
            },
            "memory_hit_rate": {
                "expr": 'cache_hit_ratio{cache_type="memory"}',
                "legendFormat": "Memory Hit Rate %",
            },
            "redis_hits": {
                "expr": 'rate(cache_hits_total{cache_type="redis"}[5m])',
                "legendFormat": "Redis Hits/sec",
            },
            "redis_misses": {
                "expr": 'rate(cache_misses_total{cache_type="redis"}[5m])',
                "legendFormat": "Redis Misses/sec",
            },
            "memory_hits": {
                "expr": 'rate(cache_hits_total{cache_type="memory"}[5m])',
                "legendFormat": "Memory Hits/sec",
            },
            "memory_misses": {
                "expr": 'rate(cache_misses_total{cache_type="memory"}[5m])',
                "legendFormat": "Memory Misses/sec",
            },
            "redis_response_time": {
                "expr": (
                    "histogram_quantile(0.95, rate("
                    'cache_operation_duration_seconds_bucket{cache_type="redis"}[5m])) * 1000'
                ),
                "legendFormat": "Redis P95",
            },
            "memory_response_time": {
                "expr": (
                    "histogram_quantile(0.95, rate("
                    'cache_operation_duration_seconds_bucket{cache_type="memory"}[5m])) * 1000'
                ),
                "legendFormat": "Memory P95",
            },
        }

    @staticmethod
    def get_system_health_queries() -> Dict[str, Dict[str, Any]]:
        """Get system health metric queries"""
        return {
            "cpu_usage": {
                "expr": "system_cpu_usage_percent",
                "legendFormat": "CPU Usage %",
            },
            "memory_usage": {
                "expr": "system_memory_usage_bytes / system_memory_total_bytes * 100",
                "legendFormat": "Memory Usage %",
            },
            "network_out": {
                "expr": "rate(system_network_bytes_sent[5m]) * 8 / 1024 / 1024",
                "legendFormat": "Outbound Mbps",
            },
            "network_in": {
                "expr": "rate(system_network_bytes_recv[5m]) * 8 / 1024 / 1024",
                "legendFormat": "Inbound Mbps",
            },
            "http_connections": {
                "expr": 'system_active_connections{type="http"}',
                "legendFormat": "HTTP Connections",
            },
            "db_connections": {
                "expr": 'system_active_connections{type="database"}',
                "legendFormat": "Database Connections",
            },
        }

    @staticmethod
    def get_business_impact_queries() -> Dict[str, Dict[str, Any]]:
        """Get business impact metric queries"""
        return {
            "successful_logins": {
                "expr": 'rate(auth_login_attempts_total{status="success"}[5m]) * 100',
                "legendFormat": "Successful Logins/min",
            },
            "failed_logins": {
                "expr": "rate(auth_login_failures_total[5m]) * 100",
                "legendFormat": "Failed Logins/min",
            },
            "active_sessions": {
                "expr": "auth_active_sessions",
                "legendFormat": "Active Sessions",
            },
            "login_improvement": {
                "expr": '((2500 - auth_login_duration_seconds{quantile="0.95"} * 1000) / 2500) * 100',
                "legendFormat": "Login Improvement vs Baseline %",
            },
            "context_switch_improvement": {
                "expr": '((1500 - auth_context_switch_duration_seconds{quantile="0.95"} * 1000) / 1500) * 100',
                "legendFormat": "Context Switch Improvement %",
            },
        }

    @staticmethod
    def get_performance_targets_queries() -> Dict[str, Dict[str, Any]]:
        """Get performance target achievement queries"""
        return {
            "login_target": {
                "expr": (
                    'min(100, max(0, (500 - auth_login_duration_seconds{quantile="0.95"} * '
                    "1000) / 500 * 100))"
                ),
                "legendFormat": "Login Target Achievement %",
            },
            "context_switch_target": {
                "expr": (
                    "min(100, max(0, (300 - auth_context_switch_duration_seconds{"
                    'quantile="0.95"} * 1000) / 300 * 100))'
                ),
                "legendFormat": "Context Switch Target Achievement %",
            },
            "cache_target": {
                "expr": "min(100, cache_hit_ratio / 85 * 100)",
                "legendFormat": "Cache Target Achievement %",
            },
            "system_health_score": {
                "expr": (
                    "(avg(100 - system_cpu_usage_percent) + "
                    "avg(100 - system_memory_usage_bytes / system_memory_total_bytes * 100) + "
                    "avg(cache_hit_ratio)) / 3"
                ),
                "legendFormat": "System Health Score %",
            },
        }
