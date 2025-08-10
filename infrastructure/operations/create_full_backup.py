#!/usr/bin/env python3
"""
Full System Backup Creation Script
Creates comprehensive backup before legacy code cleanup operations.
"""

import os
import sys
import json
import subprocess
import shutil
import tempfile
import stat
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, unquote
from contextlib import contextmanager
from typing import Dict, Any

# Add backend path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.core.config import settings

    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False
    print("⚠️  Async database imports unavailable - database backup will be manual")


class SecureCredentialHandler:
    """Secure credential handling for database operations."""

    @staticmethod
    @contextmanager
    def create_pgpass_file(
        host: str, port: str, database: str, username: str, password: str
    ):
        """Create temporary .pgpass file with secure permissions."""
        pgpass_content = f"{host}:{port}:{database}:{username}:{password}\n"

        # Create temporary file with secure permissions
        fd, temp_pgpass = tempfile.mkstemp(prefix="pgpass_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(pgpass_content)

            # Set secure permissions (read/write for owner only)
            os.chmod(temp_pgpass, stat.S_IRUSR | stat.S_IWUSR)

            # Set PGPASSFILE environment variable
            original_pgpassfile = os.environ.get("PGPASSFILE")
            os.environ["PGPASSFILE"] = temp_pgpass

            yield temp_pgpass

        finally:
            # Clean up
            if original_pgpassfile is not None:
                os.environ["PGPASSFILE"] = original_pgpassfile
            elif "PGPASSFILE" in os.environ:
                del os.environ["PGPASSFILE"]

            # Securely remove temporary file
            try:
                os.unlink(temp_pgpass)
            except OSError:
                pass

    @staticmethod
    def parse_database_url(db_url: str) -> Dict[str, str]:
        """Securely parse database URL with proper error handling."""
        if not db_url:
            raise ValueError("Database URL is empty")

        try:
            # Parse URL using urllib.parse for proper handling
            parsed = urlparse(db_url)

            if parsed.scheme not in ("postgresql", "postgres"):
                raise ValueError(f"Unsupported database scheme: {parsed.scheme}")

            if not parsed.hostname:
                raise ValueError("Database hostname not found in URL")

            # Extract and decode URL components
            host = parsed.hostname
            port = str(parsed.port) if parsed.port else "5432"
            database = parsed.path.lstrip("/") if parsed.path else "postgres"
            username = unquote(parsed.username) if parsed.username else ""
            password = unquote(parsed.password) if parsed.password else ""

            # Validate required components
            if not username:
                raise ValueError("Database username not found in URL")

            return {
                "host": host,
                "port": port,
                "database": database,
                "username": username,
                "password": password,
            }

        except Exception as e:
            # Sanitize error message to avoid credential exposure
            if "password" in str(e).lower() or "@" in str(e):
                raise ValueError("Failed to parse database URL: Invalid URL format")
            raise ValueError(f"Failed to parse database URL: {str(e)}")

    @staticmethod
    def sanitize_error_message(error_msg: str) -> str:
        """Remove potential credentials from error messages."""
        import re

        # Remove patterns that might contain credentials
        patterns = [
            r"password[=:]\s*[^\s]+",
            r"://[^@]*:[^@]*@",  # Remove user:pass@ from URLs
            r"PGPASSWORD[=:]\s*[^\s]+",
            r"--password[=\s]+[^\s]+",
        ]

        sanitized = error_msg
        for pattern in patterns:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)

        return sanitized


class SystemBackupManager:
    def __init__(self, backup_dir: str = None):
        """Initialize backup manager with optional custom backup directory."""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            # Default to project root backup directory
            project_root = Path(__file__).parent.parent.parent
            self.backup_dir = project_root / "backups" / f"pre_cleanup_{self.timestamp}"

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}
        self.errors = []

    def backup_git_state(self) -> dict:
        """Create git state backup including uncommitted changes."""
        print("📝 Backing up Git state...")

        git_backup = self.backup_dir / "git_state"
        git_backup.mkdir(exist_ok=True)

        try:
            # Save current branch and commit
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            current_branch = branch_result.stdout.strip()

            commit_result = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            )
            current_commit = commit_result.stdout.strip()

            # Save git status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )
            git_status = status_result.stdout

            # Create git state file
            git_state = {
                "branch": current_branch,
                "commit": current_commit,
                "status": git_status,
                "has_uncommitted_changes": bool(git_status.strip()),
                "timestamp": self.timestamp,
            }

            with open(git_backup / "git_state.json", "w") as f:
                json.dump(git_state, f, indent=2)

            # Create patch of uncommitted changes
            if git_status.strip():
                patch_result = subprocess.run(
                    ["git", "diff", "HEAD"], capture_output=True, text=True
                )

                with open(git_backup / "uncommitted_changes.patch", "w") as f:
                    f.write(patch_result.stdout)

            return {
                "status": "success",
                "branch": current_branch,
                "commit": current_commit[:8],
                "uncommitted_changes": bool(git_status.strip()),
                "backup_location": str(git_backup),
            }

        except subprocess.CalledProcessError as e:
            error = f"Git backup failed: {e}"
            self.errors.append(error)
            return {"status": "failed", "error": error}

    def backup_database(self) -> dict:
        """Create database backup using pg_dump with secure credential handling."""
        print("🗄️  Backing up database...")

        db_backup = self.backup_dir / "database"
        db_backup.mkdir(exist_ok=True)

        try:
            # Extract database connection info from environment or settings
            db_url = os.getenv("DATABASE_URL")
            if not db_url and ASYNC_AVAILABLE and hasattr(settings, "DATABASE_URL"):
                db_url = settings.DATABASE_URL

            if not db_url:
                return {"status": "skipped", "reason": "DATABASE_URL not found"}

            # Parse database URL using secure parser
            try:
                db_params = SecureCredentialHandler.parse_database_url(db_url)
            except ValueError as e:
                error = f"Database URL parsing failed: {str(e)}"
                self.errors.append(error)
                return {"status": "failed", "error": error}

            # Create backup file path
            backup_file = db_backup / f"database_backup_{self.timestamp}.sql"

            # Use secure credential handling with temporary .pgpass file
            with SecureCredentialHandler.create_pgpass_file(
                host=db_params["host"],
                port=db_params["port"],
                database=db_params["database"],
                username=db_params["username"],
                password=db_params["password"],
            ):
                # Create pg_dump command without credentials in command line or environment
                cmd = [
                    "pg_dump",
                    "-h",
                    db_params["host"],
                    "-p",
                    db_params["port"],
                    "-U",
                    db_params["username"],
                    "-d",
                    db_params["database"],
                    "--verbose",
                    "--no-owner",
                    "--no-privileges",
                    "-f",
                    str(backup_file),
                ]

                # Run pg_dump with clean environment (no credential exposure)
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    env=os.environ.copy(),  # Uses PGPASSFILE set by context manager
                )

                if result.returncode == 0:
                    # Get backup file size
                    backup_size = backup_file.stat().st_size

                    return {
                        "status": "success",
                        "backup_file": str(backup_file),
                        "size_bytes": backup_size,
                        "size_mb": round(backup_size / 1024 / 1024, 2),
                        "host": db_params["host"],  # Safe to include non-sensitive info
                        "database": db_params["database"],
                    }
                else:
                    # Sanitize error message to remove potential credentials
                    sanitized_error = SecureCredentialHandler.sanitize_error_message(
                        result.stderr
                    )
                    error = f"pg_dump failed: {sanitized_error}"
                    self.errors.append(error)
                    return {"status": "failed", "error": error}

        except Exception as e:
            # Sanitize error message to prevent credential exposure
            sanitized_error = SecureCredentialHandler.sanitize_error_message(str(e))
            error = f"Database backup failed: {sanitized_error}"
            self.errors.append(error)
            return {"status": "failed", "error": error}

    def backup_configuration_files(self) -> dict:
        """Backup critical configuration files."""
        print("⚙️  Backing up configuration files...")

        config_backup = self.backup_dir / "configuration"
        config_backup.mkdir(exist_ok=True)

        # List of critical config files to backup
        config_files = [
            ".env",
            ".env.local",
            "backend/app/core/config.py",
            "docker-compose.yml",
            "docker-compose.dev.yml",
            "docker-compose.prod.yml",
            "backend/requirements.txt",
            "package.json",
            ".pre-commit-config.yaml",
            ".github/workflows/enforce-policies.yml",
            "backend/app/middleware/legacy_endpoint_guard.py",
        ]

        backed_up_files = []
        skipped_files = []

        project_root = Path(__file__).parent.parent.parent

        for config_file in config_files:
            source_path = project_root / config_file

            if source_path.exists():
                try:
                    # Create directory structure in backup
                    backup_file_path = config_backup / config_file
                    backup_file_path.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file
                    shutil.copy2(source_path, backup_file_path)
                    backed_up_files.append(config_file)

                except Exception as e:
                    self.errors.append(f"Failed to backup {config_file}: {e}")
                    skipped_files.append(config_file)
            else:
                skipped_files.append(config_file)

        return {
            "status": "success",
            "backed_up_count": len(backed_up_files),
            "skipped_count": len(skipped_files),
            "backed_up_files": backed_up_files,
            "backup_location": str(config_backup),
        }

    def backup_legacy_code_references(self) -> dict:
        """Backup files that contain legacy code references before cleanup."""
        print("🔍 Backing up legacy code references...")

        legacy_backup = self.backup_dir / "legacy_references"
        legacy_backup.mkdir(exist_ok=True)

        # Files identified as containing legacy references
        legacy_files = [
            "backend/app/middleware/cache_middleware.py",
            "backend/app/core/rbac_middleware.py",
            "backend/app/api/v1/endpoints/monitoring/agent_monitoring.py",
            "backend/app/services/agent_registry/phase_agents.py",
            "backend/main.py",
            "backend/scripts/development/trigger_data_import.py",
            "backend/scripts/deployment/production_cleanup.py",
            "tests/temp/test_discovery_flow_api.py",
            "tests/temp/test_discovery_flow_api_fixed.py",
            "src/components/discovery/README.md",
        ]

        backed_up = []
        not_found = []

        project_root = Path(__file__).parent.parent.parent

        for legacy_file in legacy_files:
            source_path = project_root / legacy_file

            if source_path.exists():
                try:
                    backup_file_path = legacy_backup / legacy_file
                    backup_file_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, backup_file_path)
                    backed_up.append(legacy_file)
                except Exception as e:
                    self.errors.append(
                        f"Failed to backup legacy file {legacy_file}: {e}"
                    )
            else:
                not_found.append(legacy_file)

        return {
            "status": "success",
            "backed_up_count": len(backed_up),
            "not_found_count": len(not_found),
            "backed_up_files": backed_up,
            "not_found_files": not_found,
        }

    def create_backup_manifest(self) -> dict:
        """Create a manifest file describing the backup contents."""
        print("📋 Creating backup manifest...")

        # Sanitize results to remove sensitive information
        sanitized_results = self._sanitize_results_for_manifest(self.results)
        sanitized_errors = [
            SecureCredentialHandler.sanitize_error_message(error)
            for error in self.errors
        ]

        manifest = {
            "backup_timestamp": self.timestamp,
            "backup_directory": str(self.backup_dir),
            "created_by": "create_full_backup.py",
            "purpose": "Pre-legacy-cleanup backup",
            "components": sanitized_results,
            "errors": sanitized_errors,
            "total_errors": len(sanitized_errors),
        }

        manifest_file = self.backup_dir / "backup_manifest.json"
        with open(manifest_file, "w") as f:
            json.dump(manifest, f, indent=2, default=self._safe_json_serializer)

        # Also create a README
        readme_content = f"""# System Backup - {self.timestamp}

This backup was created before legacy discovery code cleanup.

## Contents:

- `git_state/` - Git repository state and uncommitted changes
- `database/` - PostgreSQL database dump
- `configuration/` - Critical configuration files
- `legacy_references/` - Files containing legacy code references
- `backup_manifest.json` - Detailed backup information

## Restoration Instructions:

### Git State Restoration:
```bash
git checkout {manifest.get('git_state', {}).get('branch', 'main')}
git reset --hard {manifest.get('git_state', {}).get('commit', 'HEAD')}
# Apply uncommitted changes if needed:
git apply git_state/uncommitted_changes.patch
```

### Database Restoration:
```bash
psql -h localhost -U postgres -d migration_db < database/database_backup_{self.timestamp}.sql
```

## Backup Statistics:

- Total components: {len(self.results)}
- Errors encountered: {len(self.errors)}
- Backup size: {self._calculate_backup_size()} MB

Created by: CC Specialized Agents
"""

        readme_file = self.backup_dir / "README.md"
        with open(readme_file, "w") as f:
            f.write(readme_content)

        return {
            "status": "success",
            "manifest_file": str(manifest_file),
            "readme_file": str(readme_file),
        }

    def _sanitize_results_for_manifest(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from results before including in manifest."""
        sanitized = {}
        sensitive_keys = {"password", "auth", "credential", "secret", "token"}

        for component, result in results.items():
            if isinstance(result, dict):
                sanitized_result = {}
                for key, value in result.items():
                    # Skip sensitive keys
                    if any(
                        sensitive_key in key.lower() for sensitive_key in sensitive_keys
                    ):
                        sanitized_result[key] = "[REDACTED]"
                    elif isinstance(value, str):
                        # Sanitize string values that might contain credentials
                        sanitized_result[key] = (
                            SecureCredentialHandler.sanitize_error_message(value)
                        )
                    else:
                        sanitized_result[key] = value
                sanitized[component] = sanitized_result
            else:
                sanitized[component] = result

        return sanitized

    def _safe_json_serializer(self, obj) -> str:
        """Safe JSON serializer that doesn't expose sensitive object representations."""
        if hasattr(obj, "__dict__"):
            # For custom objects, return a safe representation
            return f"<{type(obj).__name__} object>"
        return str(obj)

    def _calculate_backup_size(self) -> float:
        """Calculate total backup directory size."""
        try:
            total_size = sum(
                f.stat().st_size for f in self.backup_dir.rglob("*") if f.is_file()
            )
            return round(total_size / 1024 / 1024, 2)
        except OSError:
            return 0.0

    def run_full_backup(self) -> dict:
        """Execute complete backup process."""
        print(f"💾 Starting Full System Backup - {self.timestamp}")
        print(f"📁 Backup Location: {self.backup_dir}")
        print("=" * 60)

        # Execute backup components
        self.results["git_state"] = self.backup_git_state()
        self.results["database"] = self.backup_database()
        self.results["configuration"] = self.backup_configuration_files()
        self.results["legacy_references"] = self.backup_legacy_code_references()
        self.results["manifest"] = self.create_backup_manifest()

        # Summary
        successful_components = sum(
            1 for r in self.results.values() if r.get("status") == "success"
        )
        total_components = len(self.results)
        backup_size = self._calculate_backup_size()

        print("\n" + "=" * 60)
        print("💾 BACKUP COMPLETE")
        print("=" * 60)
        print(f"✅ Successful Components: {successful_components}/{total_components}")
        print(f"📁 Backup Location: {self.backup_dir}")
        print(f"💾 Total Size: {backup_size} MB")
        print(f"🕒 Timestamp: {self.timestamp}")

        if self.errors:
            print(f"❌ Errors: {len(self.errors)}")
            for error in self.errors:
                print(f"   • {error}")
        else:
            print("✅ No errors encountered")

        return {
            "success": len(self.errors) == 0,
            "backup_directory": str(self.backup_dir),
            "timestamp": self.timestamp,
            "components": self.results,
            "total_size_mb": backup_size,
            "error_count": len(self.errors),
            "errors": self.errors,
        }


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Create comprehensive system backup")
    parser.add_argument("--backup-dir", help="Custom backup directory")
    parser.add_argument(
        "--include-data", action="store_true", help="Include additional data backups"
    )

    args = parser.parse_args()

    try:
        backup_manager = SystemBackupManager(args.backup_dir)
        results = backup_manager.run_full_backup()

        if results["success"]:
            print("\n🎉 Backup completed successfully!")
            print(f"📂 Location: {results['backup_directory']}")
            sys.exit(0)
        else:
            print(f"\n⚠️  Backup completed with {results['error_count']} errors")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Backup interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Backup failed: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
