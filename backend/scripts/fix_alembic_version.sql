-- Fix alembic version table to allow longer version strings
CREATE SCHEMA IF NOT EXISTS migration;

-- Drop existing alembic_version table if it exists
DROP TABLE IF EXISTS migration.alembic_version CASCADE;

-- Create alembic_version table with larger version_num column
CREATE TABLE migration.alembic_version (
    version_num VARCHAR(255) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Set initial version (if needed)
-- INSERT INTO migration.alembic_version (version_num) VALUES ('001_comprehensive_initial_schema');