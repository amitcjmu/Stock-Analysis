-- Create pgvector extension if it doesn't exist
CREATE EXTENSION IF NOT EXISTS vector;

-- Create uuid-ossp extension if it doesn't exist (with proper quoting)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create migration schema
CREATE SCHEMA IF NOT EXISTS migration;

-- Set default search path to include migration schema
ALTER DATABASE migration_db SET search_path TO migration, public;

-- Any other initial database setup can go here