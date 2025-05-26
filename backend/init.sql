-- AI Force Migration Platform Database Initialization
-- This script sets up the initial database structure

-- Create database if it doesn't exist (handled by Docker)
-- CREATE DATABASE IF NOT EXISTS migration_db;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schema for application
CREATE SCHEMA IF NOT EXISTS migration;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA migration TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA migration TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA migration TO postgres;

-- Set default schema
ALTER DATABASE migration_db SET search_path TO migration, public;

-- Create initial admin user (optional)
-- This will be handled by the application's user management system

COMMENT ON DATABASE migration_db IS 'AI Force Migration Platform Database';
COMMENT ON SCHEMA migration IS 'Main application schema for migration data'; 