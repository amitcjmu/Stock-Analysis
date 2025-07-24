#!/usr/bin/env python3
"""
Backend Log Monitor - Real-time error detection and analysis
"""
import re
import subprocess

# Error patterns to monitor
ERROR_PATTERNS = {
    "CRITICAL": r"CRITICAL",
    "ERROR": r"ERROR",
    "EXCEPTION": r"Exception|exception",
    "TRACEBACK": r"Traceback|stack trace",
    "FAILED": r"FAILED|Failed|failed",
    "WARNING": r"WARNING",
    "TIMEOUT": r"timeout|Timeout",
    "DATABASE": r"database|Database|SQL|sql",
    "AUTH": r"auth|Auth|401|403|Unauthorized",
    "CREWAI": r"CrewAI|crewai|flow|Flow",
    "TENANT": r"tenant|multi-tenant|client_account|X-Client-Account-Id",
}


class LogMonitor:
    def __init__(self):
        self.error_count = {}
        self.last_error_time = {}

    def analyze_log_line(self, line):
        """Analyze a single log line for errors"""
        results = []

        for pattern_name, pattern in ERROR_PATTERNS.items():
            if re.search(pattern, line, re.IGNORECASE):
                # Extract timestamp
                timestamp_match = re.match(
                    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})", line
                )
                timestamp = timestamp_match.group(1) if timestamp_match else "Unknown"

                # Extract module/component
                module_match = re.search(r" - ([\w\.]+) - ", line)
                module = module_match.group(1) if module_match else "Unknown"

                # Extract log level
                level_match = re.search(
                    r" - (INFO|WARNING|ERROR|CRITICAL|DEBUG) - ", line
                )
                level = level_match.group(1) if level_match else "Unknown"

                results.append(
                    {
                        "timestamp": timestamp,
                        "level": level,
                        "module": module,
                        "pattern": pattern_name,
                        "message": line.strip(),
                    }
                )

        return results

    def format_error_report(self, error_info):
        """Format error for reporting"""
        return f"""
=== ERROR DETECTED ===
Timestamp: {error_info['timestamp']}
Level: {error_info['level']}
Module: {error_info['module']}
Pattern: {error_info['pattern']}
Message: {error_info['message'][:200]}...
=====================
"""

    def monitor_logs(self):
        """Continuously monitor Docker logs"""
        print("🔍 Starting Backend Log Monitor...")
        print("=" * 80)

        # Start tailing Docker logs
        cmd = ["docker", "logs", "-f", "--tail=50", "migration_backend"]
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        try:
            for line in process.stdout:
                errors = self.analyze_log_line(line)

                for error in errors:
                    # Skip INFO level logs unless they contain critical patterns
                    if error["level"] == "INFO" and error["pattern"] not in [
                        "FAILED",
                        "EXCEPTION",
                    ]:
                        continue

                    # Track error frequency
                    error_key = f"{error['module']}:{error['pattern']}"
                    self.error_count[error_key] = self.error_count.get(error_key, 0) + 1

                    # Print error report
                    print(self.format_error_report(error))

                    # Special handling for critical errors
                    if error["level"] in ["ERROR", "CRITICAL"]:
                        print("🚨 CRITICAL ERROR DETECTED! 🚨")

                        # Check for specific critical patterns
                        if "UUID is not JSON serializable" in error["message"]:
                            print("⚠️  ISSUE: UUID serialization error in flow creation")
                            print("📍 LOCATION: Flow Execution Engine")
                            print(
                                "🔧 LIKELY FIX: Convert UUID to string before JSON serialization"
                            )

                        elif "Client account context is required" in error["message"]:
                            print("⚠️  ISSUE: Missing multi-tenant headers")
                            print("📍 LOCATION: API middleware")
                            print(
                                "🔧 LIKELY FIX: Ensure X-Client-Account-Id header is included"
                            )

                        elif "engagement_id" in error["message"]:
                            print("⚠️  ISSUE: Missing engagement_id in context")
                            print("📍 LOCATION: User service context creation")
                            print("🔧 LIKELY FIX: Check engagement context propagation")

        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        finally:
            process.terminate()

            # Print summary
            print("\n" + "=" * 80)
            print("📊 ERROR SUMMARY:")
            for error_key, count in sorted(
                self.error_count.items(), key=lambda x: x[1], reverse=True
            ):
                module, pattern = error_key.split(":")
                print(f"  - {module} [{pattern}]: {count} occurrences")


if __name__ == "__main__":
    monitor = LogMonitor()
    monitor.monitor_logs()
