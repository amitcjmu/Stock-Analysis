#!/usr/bin/env python3
"""
Archive Legacy Session Handlers Script
Moves legacy session-based handlers to an archive directory for V2 migration cleanup.
"""

import shutil
from datetime import datetime
from pathlib import Path

# Define paths
BACKEND_ROOT = Path(__file__).parent.parent
SESSION_HANDLERS_DIR = BACKEND_ROOT / "app" / "services" / "session_handlers"
ARCHIVE_DIR = BACKEND_ROOT / "archive" / "legacy_session_handlers"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


def create_archive_directory():
    """Create archive directory structure."""
    archive_path = ARCHIVE_DIR / TIMESTAMP
    archive_path.mkdir(parents=True, exist_ok=True)
    return archive_path


def create_archive_readme(archive_path: Path):
    """Create README file explaining the archive."""
    readme_content = f"""# Legacy Session Handlers Archive

**Archived on:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Reason:** V2 Discovery Flow migration - replacing session-based architecture with flow-based

## What was archived

This directory contains the legacy session management handlers that were used in the V1
session-based discovery flow architecture. These have been replaced by the V2 flow-based
architecture using `flow_id` as the primary identifier.

### Archived Components:
- `session_handlers/` - Complete session handler directory
- Session-based CRUD operations
- Context handlers for session management
- Legacy session lifecycle management

### Replacement Components:
- `DiscoveryFlowService` - V2 flow management service
- `DiscoveryFlowCleanupServiceV2` - V2 cleanup operations
- Flow-based repositories and services

## Migration Notes

- All new implementations should use V2 flow-based patterns
- V1 session-based endpoints are maintained for backward compatibility
- Legacy code is preserved here for reference and potential rollback

## Related Files

The following files were also marked as deprecated but not archived:
- `session_management_service.py` - Marked deprecated, kept for V1 compatibility
- `workflow_state_service.py` - Marked deprecated, kept for V1 compatibility

## Contact

For questions about this migration, refer to the V2 Discovery Flow implementation documentation.
"""

    readme_path = archive_path / "README.md"
    with open(readme_path, "w") as f:
        f.write(readme_content)

    print(f"✅ Created archive README: {readme_path}")


def archive_session_handlers():
    """Archive the session handlers directory."""
    if not SESSION_HANDLERS_DIR.exists():
        print(f"⚠️ Session handlers directory not found: {SESSION_HANDLERS_DIR}")
        return False

    # Create archive directory
    archive_path = create_archive_directory()

    # Copy session handlers to archive
    destination = archive_path / "session_handlers"
    shutil.copytree(SESSION_HANDLERS_DIR, destination)
    print(f"✅ Archived session handlers to: {destination}")

    # Create archive README
    create_archive_readme(archive_path)

    # Remove original directory
    shutil.rmtree(SESSION_HANDLERS_DIR)
    print(f"✅ Removed original session handlers directory: {SESSION_HANDLERS_DIR}")

    return True


def update_imports():
    """Update imports that reference the archived session handlers."""
    # This would scan for imports and update them, but since we're keeping
    # the session_management_service.py for backward compatibility, we'll
    # just add conditional imports there

    print("⚠️ Manual action required:")
    print(
        "   - Update session_management_service.py to handle missing session_handlers"
    )
    print("   - Add conditional imports for graceful degradation")
    print("   - Test V1 endpoints still work with archived handlers")


def main():
    """Main archive process."""
    print("🗂️ Starting legacy session handlers archive process...")
    print(f"Source: {SESSION_HANDLERS_DIR}")
    print(f"Archive: {ARCHIVE_DIR}")

    # Confirm with user
    response = input("\nProceed with archiving legacy session handlers? (y/N): ")
    if response.lower() != "y":
        print("❌ Archive process cancelled")
        return

    # Perform archive
    if archive_session_handlers():
        print("\n✅ Legacy session handlers archived successfully!")
        print("\n📋 Next steps:")
        print("1. Update session_management_service.py imports")
        print("2. Test V1 endpoints for backward compatibility")
        print("3. Update documentation to reflect V2 migration")
        print("4. Consider gradual migration of V1 users to V2")
    else:
        print("\n❌ Archive process failed")


if __name__ == "__main__":
    main()
