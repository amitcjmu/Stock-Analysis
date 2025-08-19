"""
DEPRECATED: Main data cleansing test file.

This file has been split into smaller modules for maintainability:
- test_data_cleansing_stats.py - Stats endpoint tests
- test_data_cleansing_analysis.py - Analysis endpoint tests
- test_data_cleansing_fixtures.py - Shared fixtures

Note: This file is kept minimal to avoid pre-commit file length violations.
For actual tests, use the modularized files above.
"""

# Import base fixtures for compatibility if this file is still used
from test_data_cleansing_fixtures import DataCleansingTestFixtures


class TestDataCleansingEndpoints(DataCleansingTestFixtures):
    """Legacy test class - actual tests moved to modularized files"""

    def test_placeholder(self):
        """Placeholder test to keep the class valid"""
        assert True, "Tests moved to modularized files"
