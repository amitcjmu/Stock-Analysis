-- Test Database Initialization for Assessment Flow
-- This file sets up the test database with necessary extensions and sample data

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create test schemas
CREATE SCHEMA IF NOT EXISTS test_data;

-- Set up basic test configuration
SET timezone = 'UTC';

-- Insert minimal test data that tests can rely on
-- This will be expanded by individual test fixtures

-- Test client account
INSERT INTO client_accounts (id, name, status, contact_email, created_at)
VALUES
    ('11111111-1111-1111-1111-111111111111', 'Test Client Account', 'active', 'test@example.com', NOW())
ON CONFLICT (id) DO NOTHING;

-- Test engagement
INSERT INTO engagements (id, client_account_id, name, description, status, created_at)
VALUES
    ('22222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', 'Test Engagement', 'Test engagement for assessment flow', 'active', NOW())
ON CONFLICT (id) DO NOTHING;

-- Test user profile
INSERT INTO user_profiles (id, email, full_name, status, client_account_id, created_at)
VALUES
    ('33333333-3333-3333-3333-333333333333', 'testuser@example.com', 'Test User', 'active', '11111111-1111-1111-1111-111111111111', NOW())
ON CONFLICT (id) DO NOTHING;

-- Test data import session for sample applications
INSERT INTO data_import_sessions (id, client_account_id, engagement_id, filename, status, total_records, created_at)
VALUES
    ('44444444-4444-4444-4444-444444444444', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', 'test_applications.csv', 'completed', 3, NOW())
ON CONFLICT (id) DO NOTHING;

-- Sample test applications
INSERT INTO assets (id, client_account_id, engagement_id, name, asset_type, hostname, ip_address, data_import_session_id, created_at)
VALUES
    ('app-1', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', 'Frontend Portal', 'application', 'frontend-portal.example.com', '192.168.1.10', '44444444-4444-4444-4444-444444444444', NOW()),
    ('app-2', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', 'Backend API', 'application', 'backend-api.example.com', '192.168.1.20', '44444444-4444-4444-4444-444444444444', NOW()),
    ('app-3', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', 'Analytics Service', 'application', 'analytics.example.com', '192.168.1.30', '44444444-4444-4444-4444-444444444444', NOW())
ON CONFLICT (id) DO NOTHING;

-- Sample test metadata for applications
UPDATE assets SET
    metadata = jsonb_build_object(
        'technology_stack', jsonb_build_object(
            'frontend', 'React 16.14.0',
            'backend', 'Node.js 14.18.0',
            'database', 'PostgreSQL 11'
        ),
        'criticality', 'high',
        'user_base', 5000,
        'data_sensitivity', 'medium'
    )
WHERE id = 'app-1';

UPDATE assets SET
    metadata = jsonb_build_object(
        'technology_stack', jsonb_build_object(
            'runtime', 'Java 8',
            'framework', 'Spring 5.2.0',
            'database', 'Oracle 12c'
        ),
        'criticality', 'critical',
        'user_base', 10000,
        'data_sensitivity', 'high'
    )
WHERE id = 'app-2';

UPDATE assets SET
    metadata = jsonb_build_object(
        'technology_stack', jsonb_build_object(
            'runtime', 'Python 3.8',
            'framework', 'Django 3.2',
            'database', 'MySQL 5.7'
        ),
        'criticality', 'medium',
        'user_base', 500,
        'data_sensitivity', 'low'
    )
WHERE id = 'app-3';

-- Create test indexes for performance
CREATE INDEX IF NOT EXISTS idx_test_assets_client_engagement
ON assets(client_account_id, engagement_id);

CREATE INDEX IF NOT EXISTS idx_test_assets_type
ON assets(asset_type);

-- Verify test data setup
DO $$
BEGIN
    -- Check that test data was created successfully
    IF NOT EXISTS (SELECT 1 FROM client_accounts WHERE id = '11111111-1111-1111-1111-111111111111') THEN
        RAISE EXCEPTION 'Test client account not created';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM engagements WHERE id = '22222222-2222-2222-2222-222222222222') THEN
        RAISE EXCEPTION 'Test engagement not created';
    END IF;

    IF (SELECT COUNT(*) FROM assets WHERE client_account_id = '11111111-1111-1111-1111-111111111111') < 3 THEN
        RAISE EXCEPTION 'Test applications not created';
    END IF;

    RAISE NOTICE 'Test database initialization completed successfully';
END $$;
