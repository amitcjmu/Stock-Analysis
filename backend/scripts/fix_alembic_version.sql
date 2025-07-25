-- Fix alembic version table to allow longer version strings
CREATE SCHEMA IF NOT EXISTS migration;

-- Only modify alembic_version table if it needs fixing
DO $$
BEGIN
    -- Check if alembic_version table exists
    IF EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'migration'
        AND table_name = 'alembic_version'
    ) THEN
        -- Check if version_num column is too small
        IF EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'migration'
            AND table_name = 'alembic_version'
            AND column_name = 'version_num'
            AND character_maximum_length < 255
        ) THEN
            -- Alter the column to allow longer version strings
            ALTER TABLE migration.alembic_version
            ALTER COLUMN version_num TYPE VARCHAR(255);
        END IF;
    ELSE
        -- Create table if it doesn't exist
        CREATE TABLE migration.alembic_version (
            version_num VARCHAR(255) NOT NULL,
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        );
    END IF;
END $$;
