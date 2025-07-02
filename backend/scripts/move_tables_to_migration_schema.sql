-- Move all tables from public schema to migration schema
-- This script will move all tables while preserving data and constraints

-- First, ensure migration schema exists
CREATE SCHEMA IF NOT EXISTS migration;

-- Move all tables from public to migration schema
DO $$
DECLARE
    tbl RECORD;
BEGIN
    -- Move each table
    FOR tbl IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename != 'spatial_ref_sys'  -- Skip PostGIS system tables
    LOOP
        EXECUTE format('ALTER TABLE public.%I SET SCHEMA migration', tbl.tablename);
        RAISE NOTICE 'Moved table % to migration schema', tbl.tablename;
    END LOOP;
END$$;

-- Update search path to include migration schema
ALTER DATABASE migration_db SET search_path TO migration, public;

-- Verify the move
SELECT 
    schemaname,
    COUNT(*) as table_count 
FROM pg_tables 
WHERE schemaname IN ('public', 'migration')
GROUP BY schemaname
ORDER BY schemaname;