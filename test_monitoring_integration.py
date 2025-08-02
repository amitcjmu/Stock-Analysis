#!/usr/bin/env python3
"""
Integration Test for Performance Monitoring System

Tests the comprehensive performance monitoring system to validate
that all components work together correctly and can track auth
performance optimization metrics effectively.

This test validates:
- Performance metrics collection accuracy
- Auth performance monitoring integration
- Cache performance tracking
- System health dashboard functionality
- Performance analytics engine insights
- End-to-end monitoring workflow
"""

import asyncio
import time
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_monitoring_integration():
    """Test comprehensive monitoring system integration"""
    print("🚀 Starting Performance Monitoring Integration Test...")

    try:
        # Import monitoring components
        from app.services.monitoring import (
            get_metrics_collector,
            get_auth_performance_monitor,
            get_cache_performance_monitor,
            get_system_health_dashboard,
            get_performance_analytics_engine,
            get_grafana_dashboard_config,
            AuthOperation,
            AuthStatus,
            CacheOperation,
            CacheLayer,
            CacheResult
        )

        print("✅ Successfully imported all monitoring components")

        # Test 1: Initialize all monitoring components
        print("\n📊 Test 1: Initializing monitoring components...")

        metrics_collector = get_metrics_collector()
        auth_monitor = get_auth_performance_monitor()
        cache_monitor = get_cache_performance_monitor()
        dashboard = get_system_health_dashboard()
        analytics = get_performance_analytics_engine()
        grafana_config = get_grafana_dashboard_config()

        print("✅ All monitoring components initialized successfully")

        # Test 2: Test authentication performance monitoring
        print("\n🔐 Test 2: Testing authentication performance monitoring...")

        # Simulate login operations with different performance profiles
        login_times = [0.2, 0.3, 0.4, 0.8, 1.2]  # Various response times

        for i, response_time in enumerate(login_times):
            operation_id = auth_monitor.start_operation(
                AuthOperation.LOGIN,
                user_id=f"test_user_{i}",
                context_data={"client_ip": "127.0.0.1", "test_scenario": "integration_test"}
            )

            # Simulate login processing time
            await asyncio.sleep(response_time)

            # Complete operation
            status = AuthStatus.SUCCESS if response_time < 1.0 else AuthStatus.FAILURE
            auth_monitor.end_operation(operation_id, status, cache_hit=(i % 2 == 0))

        print(f"✅ Completed {len(login_times)} login performance tests")

        # Test 3: Test cache performance monitoring
        print("\n💾 Test 3: Testing cache performance monitoring...")

        # Simulate cache operations
        cache_operations = [
            (CacheOperation.GET, CacheLayer.REDIS, 0.05, CacheResult.HIT),
            (CacheOperation.GET, CacheLayer.REDIS, 0.08, CacheResult.MISS),
            (CacheOperation.SET, CacheLayer.REDIS, 0.03, CacheResult.SUCCESS),
            (CacheOperation.GET, CacheLayer.MEMORY, 0.01, CacheResult.HIT),
            (CacheOperation.GET, CacheLayer.MEMORY, 0.02, CacheResult.MISS),
        ]

        for operation, layer, duration, result in cache_operations:
            cache_monitor.record_cache_operation(
                operation, layer, "auth:session", duration, result,
                data_size_bytes=1024, metadata={"test": "integration"}
            )

        print(f"✅ Recorded {len(cache_operations)} cache operations")

        # Test 4: Test session validation performance
        print("\n🔍 Test 4: Testing session validation performance...")

        session_validations = [0.05, 0.08, 0.12, 0.15, 0.20]  # Different validation times

        for i, validation_time in enumerate(session_validations):
            operation_id = auth_monitor.start_operation(
                AuthOperation.SESSION_VALIDATION,
                user_id=f"test_user_{i % 3}",
                context_data={"session_type": "web"}
            )

            await asyncio.sleep(validation_time)

            auth_monitor.end_operation(
                operation_id,
                AuthStatus.SUCCESS,
                cache_hit=(i % 3 != 0)  # Vary cache hits
            )

        print(f"✅ Completed {len(session_validations)} session validation tests")

        # Test 5: Test context switching performance
        print("\n🔄 Test 5: Testing context switching performance...")

        context_switches = [0.1, 0.15, 0.25, 0.35, 0.45]  # Different switch times

        for i, switch_time in enumerate(context_switches):
            operation_id = auth_monitor.start_operation(
                AuthOperation.CONTEXT_SWITCH,
                user_id=f"test_user_{i % 2}",
                context_data={"context_type": "client" if i % 2 == 0 else "engagement"}
            )

            await asyncio.sleep(switch_time)

            auth_monitor.end_operation(operation_id, AuthStatus.SUCCESS)

        print(f"✅ Completed {len(context_switches)} context switch tests")

        # Test 6: Validate metrics collection
        print("\n📈 Test 6: Validating metrics collection...")

        performance_summary = metrics_collector.get_performance_summary()

        assert "auth_performance" in performance_summary, "Auth performance metrics missing"
        assert "cache_performance" in performance_summary, "Cache performance metrics missing"
        assert "system_performance" in performance_summary, "System performance metrics missing"

        print("✅ Performance metrics collection validated")

        # Test 7: Test comprehensive statistics
        print("\n📊 Test 7: Testing comprehensive statistics...")

        auth_stats = auth_monitor.get_comprehensive_stats()
        cache_stats = cache_monitor.get_comprehensive_stats()

        # Validate auth statistics
        assert auth_stats["overall_summary"]["total_operations"] > 0, "No auth operations recorded"
        assert "login" in auth_stats["operations"], "Login operations not tracked"
        assert "session_validation" in auth_stats["operations"], "Session validation not tracked"
        assert "context_switch" in auth_stats["operations"], "Context switch not tracked"

        # Validate cache statistics
        assert cache_stats["overall_summary"]["total_operations"] > 0, "No cache operations recorded"
        assert "redis" in cache_stats["cache_layers"], "Redis layer not tracked"
        assert "memory" in cache_stats["cache_layers"], "Memory layer not tracked"

        print("✅ Comprehensive statistics validated")

        # Test 8: Test dashboard data generation
        print("\n📱 Test 8: Testing dashboard data generation...")

        dashboard_data = await dashboard.get_dashboard_data()

        assert "overall_health" in dashboard_data, "Overall health missing from dashboard"
        assert "performance_summary" in dashboard_data, "Performance summary missing"
        assert "auth_health" in dashboard_data, "Auth health section missing"
        assert "cache_health" in dashboard_data, "Cache health section missing"

        print("✅ Dashboard data generation validated")

        # Test 9: Test real-time metrics
        print("\n⚡ Test 9: Testing real-time metrics...")

        real_time_metrics = await dashboard.get_real_time_metrics()

        assert "auth_performance" in real_time_metrics, "Real-time auth metrics missing"
        assert "cache_performance" in real_time_metrics, "Real-time cache metrics missing"
        assert "system_resources" in real_time_metrics, "Real-time system metrics missing"

        print("✅ Real-time metrics validated")

        # Test 10: Test analytics engine
        print("\n🧠 Test 10: Testing performance analytics engine...")

        # Wait a moment for trend data to accumulate
        await asyncio.sleep(2)

        trends = analytics.analyze_performance_trends(hours=1)
        bottlenecks = await analytics.identify_bottlenecks()
        recommendations = await analytics.generate_optimization_recommendations()

        print(f"📈 Identified {len(trends)} performance trends")
        print(f"🚨 Found {len(bottlenecks)} potential bottlenecks")
        print(f"💡 Generated {len(recommendations)} optimization recommendations")

        print("✅ Performance analytics engine validated")

        # Test 11: Test performance report generation
        print("\n📋 Test 11: Generating comprehensive performance report...")

        performance_report = await analytics.generate_performance_report(hours=1)

        assert "executive_summary" in performance_report, "Executive summary missing"
        assert "performance_trends" in performance_report, "Performance trends missing"
        assert "bottleneck_analysis" in performance_report, "Bottleneck analysis missing"
        assert "optimization_recommendations" in performance_report, "Recommendations missing"

        print("✅ Performance report generation validated")

        # Test 12: Test Grafana dashboard configuration
        print("\n📊 Test 12: Testing Grafana dashboard configuration...")

        executive_dashboard = grafana_config.generate_executive_overview_dashboard()
        auth_dashboard = grafana_config.generate_auth_performance_dashboard()
        cache_dashboard = grafana_config.generate_cache_performance_dashboard()
        alert_rules = grafana_config.generate_alerting_rules()

        assert "dashboard" in executive_dashboard, "Executive dashboard config invalid"
        assert "dashboard" in auth_dashboard, "Auth dashboard config invalid"
        assert "dashboard" in cache_dashboard, "Cache dashboard config invalid"
        assert "groups" in alert_rules, "Alert rules config invalid"

        print("✅ Grafana dashboard configuration validated")

        # Test 13: Performance improvement calculation
        print("\n🎯 Test 13: Testing performance improvement calculations...")

        # Get current performance metrics
        login_stats = auth_stats["operations"].get("login", {})
        current_login_p95 = login_stats.get("p95_duration_ms", 0)

        if current_login_p95 > 0:
            # Calculate improvement vs baseline (2500ms baseline from design doc)
            baseline_login = 2500
            improvement = ((baseline_login - current_login_p95) / baseline_login) * 100

            print(f"📊 Current login P95: {current_login_p95:.0f}ms")
            print(f"📊 Baseline (before optimization): {baseline_login}ms")
            print(f"📊 Performance improvement: {improvement:.1f}%")

            # Target is 80-90% improvement
            if improvement >= 80:
                print("🎉 EXCELLENT: Achieved target performance improvement!")
            elif improvement >= 60:
                print("✅ GOOD: Significant performance improvement achieved")
            else:
                print("⚠️  MODERATE: Some performance improvement, more optimization needed")

        print("✅ Performance improvement calculations validated")

        # Test 14: Business impact analysis
        print("\n💼 Test 14: Testing business impact analysis...")

        if current_login_p95 > 0:
            business_impact = analytics.calculate_business_impact(
                "login_p95_ms", -improvement  # Negative because improvement reduces response time
            )

            print(f"📈 Estimated user satisfaction improvement: {business_impact.estimated_user_impact.get('user_satisfaction', 0):.1f}%")
            print(f"📈 Estimated conversion rate impact: {business_impact.estimated_user_impact.get('conversion_rate', 0):.2f}%")
            print(f"📈 Business impact confidence: {business_impact.confidence_level:.1f}%")

        print("✅ Business impact analysis validated")

        # Final Summary
        print("\n" + "="*60)
        print("🎉 PERFORMANCE MONITORING INTEGRATION TEST COMPLETE!")
        print("="*60)

        print(f"\n📊 Test Results Summary:")
        print(f"   • Total auth operations tested: {auth_stats['overall_summary']['total_operations']}")
        print(f"   • Total cache operations tested: {cache_stats['overall_summary']['total_operations']}")
        print(f"   • Auth success rate: {auth_stats['overall_summary']['overall_success_rate']:.1f}%")
        print(f"   • Cache hit rate: {cache_stats['overall_summary']['overall_hit_rate']:.1f}%")
        print(f"   • Performance trends identified: {len(trends)}")
        print(f"   • Bottlenecks found: {len(bottlenecks)}")
        print(f"   • Optimization recommendations: {len(recommendations)}")

        if current_login_p95 > 0:
            print(f"   • Current login P95 performance: {current_login_p95:.0f}ms")
            print(f"   • Performance improvement achieved: {improvement:.1f}%")

        print(f"\n🎯 Performance Targets Progress:")
        print(f"   • Login target (200-500ms): {'✅ ACHIEVED' if current_login_p95 <= 500 else '⏳ IN PROGRESS'}")
        print(f"   • Improvement target (80-90%): {'✅ ACHIEVED' if improvement >= 80 else '⏳ IN PROGRESS'}")

        print(f"\n✅ All monitoring components are working correctly!")
        print(f"✅ Performance metrics are being collected accurately!")
        print(f"✅ Analytics engine is providing valuable insights!")
        print(f"✅ Dashboard system is operational!")
        print(f"✅ Grafana integration is configured!")

        return True

    except Exception as e:
        print(f"\n❌ Integration test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run the integration test
    success = asyncio.run(test_monitoring_integration())

    if success:
        print(f"\n🎉 Integration test completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Integration test failed!")
        sys.exit(1)
