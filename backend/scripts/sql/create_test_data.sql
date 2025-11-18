-- Create test data for unmapped assets functionality
-- This script creates assets with different types to test the include_unmapped_assets parameter

-- Use the default test tenant IDs
\set client_account_id '00000000-0000-0000-0000-000000000001'
\set engagement_id '00000000-0000-0000-0000-000000000001'

-- Create a test discovery flow if it doesn't exist
DO $$
DECLARE
    test_flow_id UUID := '11111111-1111-1111-1111-111111111111';
BEGIN
    IF NOT EXISTS (SELECT 1 FROM migration.discovery_flows WHERE flow_id = test_flow_id) THEN
        INSERT INTO migration.discovery_flows (
            flow_id,
            client_account_id,
            engagement_id,
            status,
            current_phase,
            created_at
        ) VALUES (
            test_flow_id,
            '00000000-0000-0000-0000-000000000001'::UUID,
            '00000000-0000-0000-0000-000000000001'::UUID,
            'completed',
            'complete',
            NOW()
        );
    END IF;
END $$;

-- Delete existing test assets to start fresh
DELETE FROM migration.assets
WHERE client_account_id = '00000000-0000-0000-0000-000000000001'::UUID
  AND engagement_id = '00000000-0000-0000-0000-000000000001'::UUID
  AND name LIKE 'Test-%';

-- Create test assets with different types
INSERT INTO migration.assets (
    id,
    client_account_id,
    engagement_id,
    flow_id,
    name,
    asset_type,
    discovery_status,
    assessment_readiness,
    created_at,
    updated_at
) VALUES
    -- Application assets (should NOT appear in unmapped assets)
    (
        '22222222-2222-2222-2222-222222222221'::UUID,
        '00000000-0000-0000-0000-000000000001'::UUID,
        '00000000-0000-0000-0000-000000000001'::UUID,
        '11111111-1111-1111-1111-111111111111'::UUID,
        'Test-CRM-Application',
        'application',
        'completed',
        'ready',
        NOW(),
        NOW()
    ),
    (
        '22222222-2222-2222-2222-222222222222'::UUID,
        '00000000-0000-0000-0000-000000000001'::UUID,
        '00000000-0000-0000-0000-000000000001'::UUID,
        '11111111-1111-1111-1111-111111111111'::UUID,
        'Test-ERP-Application',
        'application',
        'completed',
        'ready',
        NOW(),
        NOW()
    ),
    -- Database assets (SHOULD appear in unmapped assets)
    (
        '33333333-3333-3333-3333-333333333331'::UUID,
        '00000000-0000-0000-0000-000000000001'::UUID,
        '00000000-0000-0000-0000-000000000001'::UUID,
        '11111111-1111-1111-1111-111111111111'::UUID,
        'Test-MySQL-Database',
        'database',
        'completed',
        'ready',
        NOW(),
        NOW()
    ),
    (
        '33333333-3333-3333-3333-333333333332'::UUID,
        '00000000-0000-0000-0000-000000000001'::UUID,
        '00000000-0000-0000-0000-000000000001'::UUID,
        '11111111-1111-1111-1111-111111111111'::UUID,
        'Test-PostgreSQL-Database',
        'database',
        'completed',
        'partial',
        NOW(),
        NOW()
    ),
    -- Server assets (SHOULD appear in unmapped assets)
    (
        '44444444-4444-4444-4444-444444444441'::UUID,
        '00000000-0000-0000-0000-000000000001'::UUID,
        '00000000-0000-0000-0000-000000000001'::UUID,
        '11111111-1111-1111-1111-111111111111'::UUID,
        'Test-Web-Server-01',
        'server',
        'completed',
        'ready',
        NOW(),
        NOW()
    ),
    (
        '44444444-4444-4444-4444-444444444442'::UUID,
        '00000000-0000-0000-0000-000000000001'::UUID,
        '00000000-0000-0000-0000-000000000001'::UUID,
        '11111111-1111-1111-1111-111111111111'::UUID,
        'Test-App-Server-02',
        'server',
        'in_progress',
        'not_ready',
        NOW(),
        NOW()
    ),
    -- Network devices (SHOULD appear in unmapped assets)
    (
        '55555555-5555-5555-5555-555555555551'::UUID,
        '00000000-0000-0000-0000-000000000001'::UUID,
        '00000000-0000-0000-0000-000000000001'::UUID,
        '11111111-1111-1111-1111-111111111111'::UUID,
        'Test-Router-01',
        'network',
        'completed',
        'ready',
        NOW(),
        NOW()
    ),
    (
        '55555555-5555-5555-5555-555555555552'::UUID,
        '00000000-0000-0000-0000-000000000001'::UUID,
        '00000000-0000-0000-0000-000000000001'::UUID,
        '11111111-1111-1111-1111-111111111111'::UUID,
        'Test-Switch-01',
        'network',
        'completed',
        'ready',
        NOW(),
        NOW()
    );

-- Create a canonical application and link one of the databases to it
INSERT INTO migration.canonical_applications (
    id,
    client_account_id,
    engagement_id,
    canonical_name,
    normalized_name,
    usage_count,
    created_at,
    updated_at
) VALUES (
    '66666666-6666-6666-6666-666666666661'::UUID,
    '00000000-0000-0000-0000-000000000001'::UUID,
    '00000000-0000-0000-0000-000000000001'::UUID,
    'Test-CRM-System',
    'test_crm_system',
    1,
    NOW(),
    NOW()
) ON CONFLICT (client_account_id, engagement_id, normalized_name) DO UPDATE
SET usage_count = migration.canonical_applications.usage_count + 1;

-- Create a collection flow for linking
INSERT INTO migration.collection_flows (
    id,
    client_account_id,
    engagement_id,
    flow_id,
    status,
    created_at
) VALUES (
    '77777777-7777-7777-7777-777777777771'::UUID,
    '00000000-0000-0000-0000-000000000001'::UUID,
    '00000000-0000-0000-0000-000000000001'::UUID,
    '88888888-8888-8888-8888-888888888881'::UUID,
    'completed',
    NOW()
) ON CONFLICT DO NOTHING;

-- Link the MySQL database to the canonical application
INSERT INTO migration.collection_flow_applications (
    id,
    collection_flow_id,
    asset_id,
    application_name,
    canonical_application_id,
    client_account_id,
    engagement_id,
    collection_status,
    match_confidence,
    created_at
) VALUES (
    '99999999-9999-9999-9999-999999999991'::UUID,
    '77777777-7777-7777-7777-777777777771'::UUID,
    '33333333-3333-3333-3333-333333333331'::UUID,  -- MySQL database
    'Test-CRM-System',
    '66666666-6666-6666-6666-666666666661'::UUID,  -- Canonical app
    '00000000-0000-0000-0000-000000000001'::UUID,
    '00000000-0000-0000-0000-000000000001'::UUID,
    'completed',
    0.95,
    NOW()
) ON CONFLICT DO NOTHING;

-- Verify the data
SELECT
    'Applications' AS result_type,
    COUNT(*) AS record_count
FROM migration.assets
WHERE client_account_id = '00000000-0000-0000-0000-000000000001'::UUID
  AND engagement_id = '00000000-0000-0000-0000-000000000001'::UUID
  AND asset_type = 'application'
  AND name LIKE 'Test-%'
UNION ALL
SELECT
    'Non-application assets' AS result_type,
    COUNT(*) AS record_count
FROM migration.assets
WHERE client_account_id = '00000000-0000-0000-0000-000000000001'::UUID
  AND engagement_id = '00000000-0000-0000-0000-000000000001'::UUID
  AND asset_type != 'application'
  AND name LIKE 'Test-%'
UNION ALL
SELECT
    'Mapped non-app assets' AS result_type,
    COUNT(*) AS record_count
FROM migration.assets a
INNER JOIN migration.collection_flow_applications cfa ON a.id = cfa.asset_id
WHERE a.client_account_id = '00000000-0000-0000-0000-000000000001'::UUID
  AND a.engagement_id = '00000000-0000-0000-0000-000000000001'::UUID
  AND a.asset_type != 'application'
  AND a.name LIKE 'Test-%';
