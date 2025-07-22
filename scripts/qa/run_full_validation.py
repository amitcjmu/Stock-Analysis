#!/usr/bin/env python3
"""
Full Validation Test Suite

This script orchestrates all validation tests for the AI Modernize Migration Platform
after database seeding is complete.

Usage:
    python scripts/qa/run_full_validation.py [--quick] [--export-dir DIR]
"""

import asyncio
import sys
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add app path
sys.path.append('/app')

# Import validation modules
from validate_seeding import DatabaseValidator
from multi_tenant_isolation_tests import MultiTenantIsolationTester
from performance_validation import PerformanceValidator

class FullValidationSuite:
    """Orchestrate all validation tests."""
    
    def __init__(self, quick_mode: bool = False, export_dir: str = None):
        self.quick_mode = quick_mode
        self.export_dir = export_dir or '/tmp/validation_reports'
        self.results = {}
        
        # Create export directory if it doesn't exist
        Path(self.export_dir).mkdir(parents=True, exist_ok=True)
        
    async def run_full_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation test suite."""
        print("🚀 Starting Full Validation Test Suite")
        print("=" * 60)
        print(f"📅 Started at: {datetime.now().isoformat()}")
        print(f"⚡ Quick Mode: {'Enabled' if self.quick_mode else 'Disabled'}")
        print(f"📁 Export Directory: {self.export_dir}")
        print()
        
        start_time = datetime.now()
        
        try:
            # 1. Database Seeding Validation
            print("1️⃣ Running Database Seeding Validation...")
            await self._run_seeding_validation()
            
            # 2. Multi-Tenant Isolation Tests
            print("\n2️⃣ Running Multi-Tenant Isolation Tests...")
            await self._run_isolation_tests()
            
            # 3. Performance Validation (skip in quick mode)
            if not self.quick_mode:
                print("\n3️⃣ Running Performance Validation...")
                await self._run_performance_tests()
            else:
                print("\n3️⃣ Skipping Performance Tests (Quick Mode)")
                self.results['performance'] = {
                    'skipped': True,
                    'reason': 'Quick mode enabled'
                }
            
            # 4. Generate consolidated report
            print("\n4️⃣ Generating Consolidated Report...")
            consolidated_report = self._generate_consolidated_report(start_time)
            
            # 5. Export all reports
            await self._export_reports(consolidated_report)
            
            return consolidated_report
            
        except Exception as e:
            print(f"❌ Validation suite failed: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def _run_seeding_validation(self):
        """Run database seeding validation."""
        try:
            validator = DatabaseValidator(verbose=False)
            report = await validator.run_all_validations()
            self.results['seeding'] = report
            
            # Quick summary
            summary = report['summary']
            print(f"   ✅ Passed: {summary['passed']}")
            print(f"   ❌ Failed: {summary['failed']}")
            print(f"   ⚠️  Warnings: {summary['warnings']}")
            print(f"   📊 Success Rate: {summary['success_rate']:.1f}%")
            
        except Exception as e:
            print(f"   ❌ Seeding validation failed: {e}")
            self.results['seeding'] = {
                'error': str(e),
                'summary': {'passed': 0, 'failed': 1, 'warnings': 0, 'success_rate': 0}
            }
    
    async def _run_isolation_tests(self):
        """Run multi-tenant isolation tests."""
        try:
            tester = MultiTenantIsolationTester(verbose=False)
            report = await tester.run_isolation_tests()
            self.results['isolation'] = report
            
            # Quick summary
            summary = report['summary']
            print(f"   ✅ Passed: {summary['passed_tests']}")
            print(f"   ❌ Failed: {summary['failed_tests']}")
            print(f"   🏆 Isolation Score: {summary['isolation_score']:.1f}%")
            print(f"   🚨 Data Leaks: {summary['total_data_leaks']}")
            print(f"   🔒 Security: {report['security_assessment']}")
            
        except Exception as e:
            print(f"   ❌ Isolation tests failed: {e}")
            self.results['isolation'] = {
                'error': str(e),
                'summary': {'passed_tests': 0, 'failed_tests': 1, 'isolation_score': 0, 'total_data_leaks': 999},
                'security_assessment': 'CRITICAL - Tests failed to run'
            }
    
    async def _run_performance_tests(self):
        """Run performance validation tests."""
        try:
            validator = PerformanceValidator(verbose=False, benchmark_mode=self.quick_mode)
            report = await validator.run_performance_tests()
            self.results['performance'] = report
            
            # Quick summary
            summary = report['summary']
            print(f"   ✅ Passed: {summary['passed_tests']}")
            print(f"   ❌ Failed: {summary['failed_tests']}")
            print(f"   🏆 Performance Score: {summary['performance_score']:.1f}%")
            print(f"   ⏱️  Average Time: {summary['avg_execution_time']}s")
            print(f"   ⚡ Assessment: {report['performance_assessment']}")
            
        except Exception as e:
            print(f"   ❌ Performance tests failed: {e}")
            self.results['performance'] = {
                'error': str(e),
                'summary': {'passed_tests': 0, 'failed_tests': 1, 'performance_score': 0},
                'performance_assessment': 'POOR - Tests failed to run'
            }
    
    def _generate_consolidated_report(self, start_time: datetime) -> Dict[str, Any]:
        """Generate consolidated validation report."""
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        # Calculate overall metrics
        total_tests = 0
        total_passed = 0
        total_failed = 0
        critical_issues = []
        
        # Seeding validation metrics
        if 'seeding' in self.results and 'summary' in self.results['seeding']:
            seeding_summary = self.results['seeding']['summary']
            total_tests += seeding_summary.get('total_checks', 0)
            total_passed += seeding_summary.get('passed', 0)
            total_failed += seeding_summary.get('failed', 0)
            
            if seeding_summary.get('failed', 0) > 0:
                critical_issues.append(f"Database seeding has {seeding_summary['failed']} failed validations")
        
        # Isolation test metrics
        if 'isolation' in self.results and 'summary' in self.results['isolation']:
            isolation_summary = self.results['isolation']['summary']
            total_tests += isolation_summary.get('total_tests', 0)
            total_passed += isolation_summary.get('passed_tests', 0)
            total_failed += isolation_summary.get('failed_tests', 0)
            
            if isolation_summary.get('total_data_leaks', 0) > 0:
                critical_issues.append(f"Multi-tenant isolation has {isolation_summary['total_data_leaks']} data leaks")
        
        # Performance test metrics
        if 'performance' in self.results and not self.results['performance'].get('skipped', False):
            if 'summary' in self.results['performance']:
                perf_summary = self.results['performance']['summary']
                total_tests += perf_summary.get('total_tests', 0)
                total_passed += perf_summary.get('passed_tests', 0)
                total_failed += perf_summary.get('failed_tests', 0)
                
                if perf_summary.get('failed_tests', 0) > 5:  # Allow some performance variance
                    critical_issues.append(f"Performance validation has {perf_summary['failed_tests']} slow queries")
        
        # Determine overall status
        overall_status = self._determine_overall_status(critical_issues)
        
        # Calculate success rate
        success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
        
        consolidated_report = {
            "validation_metadata": {
                "suite_version": "1.0.0",
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "total_duration_seconds": round(total_duration, 2),
                "quick_mode": self.quick_mode,
                "export_directory": self.export_dir
            },
            "overall_summary": {
                "status": overall_status,
                "total_tests": total_tests,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "overall_success_rate": round(success_rate, 1),
                "critical_issues_count": len(critical_issues),
                "ready_for_demo": len(critical_issues) == 0 and total_failed <= 5
            },
            "component_results": {
                "database_seeding": self._extract_component_summary('seeding'),
                "multi_tenant_isolation": self._extract_component_summary('isolation'),
                "performance_validation": self._extract_component_summary('performance')
            },
            "critical_issues": critical_issues,
            "recommendations": self._generate_overall_recommendations(),
            "detailed_results": self.results
        }
        
        return consolidated_report
    
    def _determine_overall_status(self, critical_issues: List[str]) -> str:
        """Determine overall validation status."""
        if not critical_issues:
            return "PASS - Ready for Demo"
        elif len(critical_issues) <= 2:
            return "CONDITIONAL PASS - Minor Issues"
        elif any("data leak" in issue.lower() for issue in critical_issues):
            return "FAIL - Security Issues"
        else:
            return "FAIL - Multiple Issues"
    
    def _extract_component_summary(self, component: str) -> Dict[str, Any]:
        """Extract component summary for consolidated report."""
        if component not in self.results:
            return {"status": "NOT_RUN", "reason": "Component not executed"}
        
        result = self.results[component]
        
        if 'error' in result:
            return {
                "status": "ERROR",
                "error": result['error'],
                "summary": result.get('summary', {})
            }
        
        if result.get('skipped', False):
            return {
                "status": "SKIPPED",
                "reason": result.get('reason', 'Unknown')
            }
        
        # Extract key metrics based on component type
        if component == 'seeding':
            summary = result.get('summary', {})
            return {
                "status": "PASS" if summary.get('failed', 1) == 0 else "FAIL",
                "tests": summary.get('total_checks', 0),
                "passed": summary.get('passed', 0),
                "failed": summary.get('failed', 0),
                "success_rate": summary.get('success_rate', 0)
            }
        
        elif component == 'isolation':
            summary = result.get('summary', {})
            return {
                "status": "PASS" if summary.get('total_data_leaks', 1) == 0 else "FAIL",
                "tests": summary.get('total_tests', 0),
                "passed": summary.get('passed_tests', 0),
                "failed": summary.get('failed_tests', 0),
                "data_leaks": summary.get('total_data_leaks', 0),
                "security_assessment": result.get('security_assessment', 'UNKNOWN')
            }
        
        elif component == 'performance':
            summary = result.get('summary', {})
            return {
                "status": "PASS" if summary.get('failed_tests', 1) <= 2 else "FAIL",  # Allow minor perf issues
                "tests": summary.get('total_tests', 0),
                "passed": summary.get('passed_tests', 0),
                "failed": summary.get('failed_tests', 0),
                "avg_time": summary.get('avg_execution_time', 0),
                "performance_assessment": result.get('performance_assessment', 'UNKNOWN')
            }
        
        return {"status": "UNKNOWN", "reason": "Unknown component type"}
    
    def _generate_overall_recommendations(self) -> List[str]:
        """Generate overall recommendations."""
        recommendations = []
        
        # Check seeding results
        if ('seeding' in self.results and 
            self.results['seeding'].get('summary', {}).get('failed', 0) > 0):
            recommendations.append("🔧 Fix database seeding issues before proceeding with demo")
        
        # Check isolation results
        if ('isolation' in self.results and 
            self.results['isolation'].get('summary', {}).get('total_data_leaks', 0) > 0):
            recommendations.append("🚨 URGENT: Address multi-tenant data leaks immediately")
        
        # Check performance results
        if ('performance' in self.results and 
            not self.results['performance'].get('skipped', False) and
            self.results['performance'].get('summary', {}).get('failed_tests', 0) > 5):
            recommendations.append("⚡ Consider performance optimizations for better demo experience")
        
        # General recommendations
        if not recommendations:
            recommendations.extend([
                "✅ All validations passed - system is ready for demo",
                "📋 Complete UI validation checklist manually",
                "👥 Test with actual user accounts",
                "🔄 Run periodic validation checks"
            ])
        else:
            recommendations.append("🔄 Re-run validation suite after fixing issues")
        
        return recommendations
    
    async def _export_reports(self, consolidated_report: Dict[str, Any]):
        """Export all validation reports."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export consolidated report
        consolidated_path = os.path.join(self.export_dir, f"consolidated_validation_{timestamp}.json")
        with open(consolidated_path, 'w') as f:
            json.dump(consolidated_report, f, indent=2)
        print(f"   📄 Consolidated report: {consolidated_path}")
        
        # Export individual component reports
        for component, results in self.results.items():
            if 'error' not in results and not results.get('skipped', False):
                component_path = os.path.join(self.export_dir, f"{component}_validation_{timestamp}.json")
                with open(component_path, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"   📄 {component.title()} report: {component_path}")
        
        # Create summary text file
        summary_path = os.path.join(self.export_dir, f"validation_summary_{timestamp}.txt")
        with open(summary_path, 'w') as f:
            f.write("AI FORCE MIGRATION PLATFORM - VALIDATION SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {consolidated_report['validation_metadata']['completed_at']}\n")
            f.write(f"Duration: {consolidated_report['validation_metadata']['total_duration_seconds']}s\n")
            f.write(f"Status: {consolidated_report['overall_summary']['status']}\n")
            f.write(f"Success Rate: {consolidated_report['overall_summary']['overall_success_rate']}%\n")
            f.write(f"Ready for Demo: {consolidated_report['overall_summary']['ready_for_demo']}\n\n")
            
            if consolidated_report['critical_issues']:
                f.write("CRITICAL ISSUES:\n")
                for issue in consolidated_report['critical_issues']:
                    f.write(f"- {issue}\n")
                f.write("\n")
            
            f.write("RECOMMENDATIONS:\n")
            for rec in consolidated_report['recommendations']:
                f.write(f"- {rec}\n")
        
        print(f"   📄 Summary report: {summary_path}")

def print_final_report(report: Dict[str, Any]):
    """Print final validation report."""
    print("\n" + "="*60)
    print("🚀 FULL VALIDATION SUITE REPORT")
    print("="*60)
    
    metadata = report['validation_metadata']
    summary = report['overall_summary']
    
    print(f"📅 Started: {metadata['started_at']}")
    print(f"🏁 Completed: {metadata['completed_at']}")
    print(f"⏱️ Duration: {metadata['total_duration_seconds']}s")
    print(f"⚡ Quick Mode: {metadata['quick_mode']}")
    
    print(f"\n🎯 OVERALL STATUS: {summary['status']}")
    print(f"📊 Total Tests: {summary['total_tests']}")
    print(f"✅ Passed: {summary['total_passed']}")
    print(f"❌ Failed: {summary['total_failed']}")
    print(f"🏆 Success Rate: {summary['overall_success_rate']}%")
    print(f"🚀 Demo Ready: {'YES' if summary['ready_for_demo'] else 'NO'}")
    
    # Component breakdown
    print("\n📋 COMPONENT RESULTS:")
    print("-" * 40)
    for component, results in report['component_results'].items():
        status_emoji = "✅" if results['status'] == "PASS" else "❌" if results['status'] == "FAIL" else "⚠️"
        print(f"{status_emoji} {component.replace('_', ' ').title()}: {results['status']}")
        if 'tests' in results:
            print(f"   Tests: {results['passed']}/{results['tests']} passed")
    
    # Critical issues
    if summary['critical_issues_count'] > 0:
        print(f"\n🚨 CRITICAL ISSUES ({summary['critical_issues_count']}):")
        print("-" * 40)
        for issue in report['critical_issues']:
            print(f"  • {issue}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("-" * 40)
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"{i}. {rec}")
    
    # Final verdict
    if summary['ready_for_demo']:
        print("\n🎉 VALIDATION SUCCESSFUL!")
        print("The AI Modernize Migration Platform is ready for demonstration.")
    else:
        print("\n⚠️ VALIDATION ISSUES DETECTED")
        print("Address critical issues before demo deployment.")
        
    print(f"\n📁 Detailed reports exported to: {metadata['export_directory']}")

async def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='Run full validation suite')
    parser.add_argument('--quick', '-q', action='store_true', help='Quick validation (skip performance tests)')
    parser.add_argument('--export-dir', '-e', help='Export directory for reports', default='/tmp/validation_reports')
    
    args = parser.parse_args()
    
    suite = FullValidationSuite(quick_mode=args.quick, export_dir=args.export_dir)
    
    try:
        report = await suite.run_full_validation()
        print_final_report(report)
        
        # Exit with appropriate code
        if not report['overall_summary']['ready_for_demo']:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Validation suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())