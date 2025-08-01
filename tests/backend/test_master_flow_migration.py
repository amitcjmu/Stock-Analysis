"""Test Master Flow Orchestrator Migration
Test migration rollback and data integrity for the master flow orchestrator schema changes.
"""

import os
import shutil
import tempfile
import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from alembic import command
from alembic.config import Config

# Test database URL (using SQLite for fast testing)
TEST_DATABASE_URL = "sqlite:///:memory:"


class TestMasterFlowMigration:
    """Test the master flow orchestrator migration"""

    @pytest.fixture
    def alembic_config(self):
        """Create a temporary Alembic configuration for testing"""
        # Create temporary directory for alembic
        temp_dir = tempfile.mkdtemp()

        # Copy alembic files to temp directory
        alembic_src = os.path.join(os.path.dirname(__file__), "..", "alembic")
        alembic_dest = os.path.join(temp_dir, "alembic")
        shutil.copytree(alembic_src, alembic_dest)

        # Create alembic.ini
        ini_path = os.path.join(temp_dir, "alembic.ini")
        with open(ini_path, "w") as f:
            f.write(
                f"""
[alembic]
script_location = {alembic_dest}
sqlalchemy.url = {TEST_DATABASE_URL}
            """
            )

        config = Config(ini_path)
        yield config

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def test_engine(self):
        """Create test database engine"""
        engine = create_engine(TEST_DATABASE_URL)
        yield engine
        engine.dispose()

    def test_migration_upgrade_and_downgrade(self, alembic_config, test_engine):
        """Test that migration can be applied and rolled back successfully"""
        # Run migrations up to the parent revision
        command.upgrade(alembic_config, "002_add_assessment_flow_tables")

        # Check that new columns don't exist yet
        with test_engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT sql FROM sqlite_master
                WHERE type='table' AND name='crewai_flow_state_extensions'
            """
                )
            )
            table_sql = result.scalar()
            assert "phase_transitions" not in table_sql if table_sql else True
            assert "error_history" not in table_sql if table_sql else True

        # Apply our migration
        command.upgrade(alembic_config, "master_flow_orchestrator_001")

        # Check that new columns exist
        with test_engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT sql FROM sqlite_master
                WHERE type='table' AND name='crewai_flow_state_extensions'
            """
                )
            )
            table_sql = result.scalar()
            assert "phase_transitions" in table_sql
            assert "error_history" in table_sql
            assert "retry_count" in table_sql
            assert "parent_flow_id" in table_sql
            assert "child_flow_ids" in table_sql
            assert "flow_metadata" in table_sql

        # Test downgrade
        command.downgrade(alembic_config, "002_add_assessment_flow_tables")

        # Check that columns are removed
        with test_engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT sql FROM sqlite_master
                WHERE type='table' AND name='crewai_flow_state_extensions'
            """
                )
            )
            table_sql = result.scalar()
            assert "phase_transitions" not in table_sql if table_sql else True
            assert "error_history" not in table_sql if table_sql else True

    def test_data_migration_integrity(self, alembic_config, test_engine):
        """Test that data migration preserves existing data correctly"""
        # Setup: Create tables and insert test data
        command.upgrade(alembic_config, "002_add_assessment_flow_tables")

        Session = sessionmaker(bind=test_engine)
        session = Session()

        # Insert test discovery flow
        discovery_flow_id = str(uuid.uuid4())
        session.execute(
            text(
                """
            INSERT INTO discovery_flows (
                id, flow_id, client_account_id, engagement_id, user_id,
                flow_name, status, current_phase, created_at
            ) VALUES (
                :id, :flow_id, :client_account_id, :engagement_id, :user_id,
                :flow_name, :status, :current_phase, :created_at
            )
        """
            ),
            {
                "id": str(uuid.uuid4()),
                "flow_id": discovery_flow_id,
                "client_account_id": str(uuid.uuid4()),
                "engagement_id": str(uuid.uuid4()),
                "user_id": "test_user",
                "flow_name": "Test Discovery Flow",
                "status": "active",
                "current_phase": "data_import",
                "created_at": datetime.utcnow(),
            },
        )

        # Insert test assessment flow
        assessment_id = str(uuid.uuid4())
        session.execute(
            text(
                """
            INSERT INTO assessment_flows (
                id, client_account_id, engagement_id, status, current_phase, created_at
            ) VALUES (
                :id, :client_account_id, :engagement_id, :status, :current_phase, :created_at
            )
        """
            ),
            {
                "id": assessment_id,
                "client_account_id": str(uuid.uuid4()),
                "engagement_id": str(uuid.uuid4()),
                "status": "processing",
                "current_phase": "architecture_minimums",
                "created_at": datetime.utcnow(),
            },
        )

        session.commit()

        # Apply migration
        command.upgrade(alembic_config, "master_flow_orchestrator_001")

        # Verify discovery flow was migrated
        result = session.execute(
            text(
                """
            SELECT COUNT(*) FROM crewai_flow_state_extensions
            WHERE flow_id = :flow_id AND flow_type = 'discovery'
        """
            ),
            {"flow_id": discovery_flow_id},
        )
        assert result.scalar() == 1

        # Verify assessment flow was migrated
        result = session.execute(
            text(
                """
            SELECT COUNT(*) FROM crewai_flow_state_extensions
            WHERE flow_type = 'assessment' AND flow_metadata->>'original_id' = :id
        """
            ),
            {"id": assessment_id},
        )
        assert result.scalar() == 1

        session.close()

    def test_indexes_created(self, alembic_config, test_engine):
        """Test that performance indexes are created"""
        # Apply migration
        command.upgrade(alembic_config, "master_flow_orchestrator_001")

        # Check indexes exist (SQLite uses different syntax)
        with test_engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT name FROM sqlite_master
                WHERE type='index' AND tbl_name='crewai_flow_state_extensions'
            """
                )
            )
            index_names = [row[0] for row in result]

            # Verify expected indexes exist
            expected_indexes = [
                "idx_crewai_flow_state_flow_type_status",
                "idx_crewai_flow_state_client_status",
                "idx_crewai_flow_state_created_desc",
            ]

            for expected in expected_indexes:
                assert any(
                    expected in idx for idx in index_names
                ), f"Index {expected} not found"


@pytest.mark.integration
class TestMasterFlowMigrationPostgreSQL:
    """Test migration with real PostgreSQL database (requires Docker)"""

    @pytest.fixture
    def pg_database_url(self):
        """PostgreSQL test database URL"""
        return "postgresql://postgres:postgres@localhost:5432/test_migration"

    @pytest.mark.skipif(
        not os.environ.get("RUN_POSTGRESQL_TESTS"),
        reason="PostgreSQL tests require RUN_POSTGRESQL_TESTS=1 and running PostgreSQL",
    )
    def test_postgresql_specific_features(self, pg_database_url):
        """Test PostgreSQL-specific features like JSONB and CHECK constraints"""
        engine = create_engine(pg_database_url)

        # Create fresh database
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))

        # Run migration
        config = Config()
        config.set_main_option("script_location", "alembic")
        config.set_main_option("sqlalchemy.url", pg_database_url)

        command.upgrade(config, "master_flow_orchestrator_001")

        # Test JSONB columns
        Session = sessionmaker(bind=engine)
        session = Session()

        # Insert test data with JSONB
        test_flow_id = str(uuid.uuid4())
        session.execute(
            text(
                """
            INSERT INTO crewai_flow_state_extensions (
                id, flow_id, client_account_id, engagement_id, user_id,
                flow_type, flow_status, phase_transitions, error_history
            ) VALUES (
                :id, :flow_id, :client_account_id, :engagement_id, :user_id,
                :flow_type, :flow_status, :phase_transitions, :error_history
            )
        """
            ),
            {
                "id": str(uuid.uuid4()),
                "flow_id": test_flow_id,
                "client_account_id": str(uuid.uuid4()),
                "engagement_id": str(uuid.uuid4()),
                "user_id": "test_user",
                "flow_type": "discovery",
                "flow_status": "active",
                "phase_transitions": [
                    {"phase": "init", "timestamp": datetime.utcnow().isoformat()}
                ],
                "error_history": [],
            },
        )

        # Test CHECK constraints - should fail with invalid flow_type
        with pytest.raises(Exception):
            session.execute(
                text(
                    """
                INSERT INTO crewai_flow_state_extensions (
                    id, flow_id, client_account_id, engagement_id, user_id,
                    flow_type, flow_status
                ) VALUES (
                    :id, :flow_id, :client_account_id, :engagement_id, :user_id,
                    :flow_type, :flow_status
                )
            """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "flow_id": str(uuid.uuid4()),
                    "client_account_id": str(uuid.uuid4()),
                    "engagement_id": str(uuid.uuid4()),
                    "user_id": "test_user",
                    "flow_type": "invalid_type",  # Should fail CHECK constraint
                    "flow_status": "active",
                },
            )

        session.close()
        engine.dispose()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
