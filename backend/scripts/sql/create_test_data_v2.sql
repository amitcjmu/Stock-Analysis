-- Create test data for unmapped assets functionality
-- Uses existing Demo Corporation tenant (11111111-1111-1111-1111-111111111111)

-- Use the existing Demo Corporation tenant IDs
\set client_account_id '11111111-1111-1111-1111-111111111111'
\set engagement_id '22222222-2222-2222-2222-222222222222'

-- Delete existing test assets to start fresh
DELETE FROM migration.assets
WHERE client_account_id = '11111111-1111-1111-1111-111111111111'::UUID
  AND engagement_id = '22222222-2222-2222-2222-222222222222'::UUID
  AND name LIKE 'Test-%';

-- Create a test discovery flow if needed
DO $$
DECLARE
    test_discovery_flow_id UUID := '11111111-1111-1111-1111-111111111121';
BEGIN
    IF NOT EXISTS (SELECT 1 FROM migration.discovery_flows WHERE flow_id = test_discovery_flow_id) THEN
        -- Need to create master flow first
        INSERT INTO migration.crewai_flow_state_extensions (
            flow_id,
            client_account_id,
            engagement_id,
            flow_type,
            status,
            created_at
        ) VALUES (
            '11111111-1111-1111-1111-111111111122'::UUID,
            '11111111-1111-1111-1111-111111111111'::UUID,
            '22222222-2222-2222-2222-222222222222'::UUID,
            'discovery',
            'completed',
            NOW()
        ) ON CONFLICT DO NOTHING;

        INSERT INTO migration.discovery_flows (
            id,
            flow_id,
            master_flow_id,
            client_account_id,
            engagement_id,
            status,
            current_phase,
            created_at
        ) VALUES (
            gen_random_uuid(),
            test_discovery_flow_id,
            '11111111-1111-1111-1111-111111111122'::UUID,
            '11111111-1111-1111-1111-111111111111'::UUID,
            '22222222-2222-2222-2222-222222222222'::UUID,
            'completed',
            'complete',
            NOW()
        ) ON CONFLICT DO NOTHING;
    END IF;
END $$;

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
        '11111111-1111-1111-1111-111111111111'::UUID,
        '22222222-2222-2222-2222-222222222222'::UUID,
        '11111111-1111-1111-1111-111111111121'::UUID,
        'Test-CRM-Application',
        'application',
        'completed',
        'ready',
        NOW(),
        NOW()
    ),
    (
        '22222222-2222-2222-2222-222222222222'::UUID,
        '11111111-1111-1111-1111-111111111111'::UUID,
        '22222222-2222-2222-2222-222222222222'::UUID,
        '11111111-1111-1111-1111-111111111121'::UUID,
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
        '11111111-1111-1111-1111-111111111111'::UUID,
        '22222222-2222-2222-2222-222222222222'::UUID,
        '11111111-1111-1111-1111-111111111121'::UUID,
        'Test-MySQL-Database',
        'database',
        'completed',
        'ready',
        NOW(),
        NOW()
    ),
    (
        '33333333-3333-3333-3333-333333333332'::UUID,
        '11111111-1111-1111-1111-111111111111'::UUID,
        '22222222-2222-2222-2222-222222222222'::UUID,
        '11111111-1111-1111-1111-111111111121'::UUID,
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
        '11111111-1111-1111-1111-111111111111'::UUID,
        '22222222-2222-2222-2222-222222222222'::UUID,
        '11111111-1111-1111-1111-111111111121'::UUID,
        'Test-Web-Server-01',
        'server',
        'completed',
        'ready',
        NOW(),
        NOW()
    ),
    (
        '44444444-4444-4444-4444-444444444442'::UUID,
        '11111111-1111-1111-1111-111111111111'::UUID,
        '22222222-2222-2222-2222-222222222222'::UUID,
        '11111111-1111-1111-1111-111111111121'::UUID,
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
        '11111111-1111-1111-1111-111111111111'::UUID,
        '22222222-2222-2222-2222-222222222222'::UUID,
        '11111111-1111-1111-1111-111111111121'::UUID,
        'Test-Router-01',
        'network',
        'completed',
        'ready',
        NOW(),
        NOW()
    ),
    (
        '55555555-5555-5555-5555-555555555552'::UUID,
        '11111111-1111-1111-1111-111111111111'::UUID,
        '22222222-2222-2222-2222-222222222222'::UUID,
        '11111111-1111-1111-1111-111111111121'::UUID,
        'Test-Switch-01',
        'network',
        'completed',
        'ready',
        NOW(),
        NOW()
    )
ON CONFLICT (id) DO NOTHING;

-- Create a canonical application and link one of the databases to it
INSERT INTO migration.canonical_applications (
    id,
    client_account_id,
    engagement_id,
    canonical_name,
    normalized_name,
    name_hash,
    usage_count,
    created_at,
    updated_at
) VALUES (
    '66666666-6666-6666-6666-666666666661'::UUID,
    '11111111-1111-1111-1111-111111111111'::UUID,
    '22222222-2222-2222-2222-222222222222'::UUID,
    'Test-CRM-System',
    'test_crm_system',
    md5('test_crm_system'),
    1,
    NOW(),
    NOW()
) ON CONFLICT (client_account_id, engagement_id, normalized_name) DO UPDATE
SET usage_count = migration.canonical_applications.usage_count + 1;

-- Create a collection flow for linking
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM migration.collection_flows WHERE id = '77777777-7777-7777-7777-777777777771'::UUID) THEN
        -- Create master flow first
        INSERT INTO migration.crewai_flow_state_extensions (
            flow_id,
            client_account_id,
            engagement_id,
            flow_type,
            status,
            created_at
        ) VALUES (
            '88888888-8888-8888-8888-888888888881'::UUID,
            '11111111-1111-1111-1111-111111111111'::UUID,
            '22222222-2222-2222-2222-222222222222'::UUID,
            'collection',
            'completed',
            NOW()
        ) ON CONFLICT DO NOTHING;

        -- Get the admin user for this client account
        INSERT INTO migration.collection_flows (
            id,
            flow_id,
            master_flow_id,
            user_id,
            client_account_id,
            engagement_id,
            status,
            created_at
        )
        SELECT
            '77777777-7777-7777-7777-777777777771'::UUID,
            gen_random_uuid(),
            '88888888-8888-8888-8888-888888888881'::UUID,
            u.id,
            '11111111-1111-1111-1111-111111111111'::UUID,
            '22222222-2222-2222-2222-222222222222'::UUID,
            'completed',
            NOW()
        FROM migration.users u
        WHERE u.client_account_id = '11111111-1111-1111-1111-111111111111'::UUID
        ORDER BY u.id
        LIMIT 1
        ON CONFLICT DO NOTHING;
    END IF;
END $$;

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
    '11111111-1111-1111-1111-111111111111'::UUID,
    '22222222-2222-2222-2222-222222222222'::UUID,
    'completed',
    0.95,
    NOW()
) ON CONFLICT DO NOTHING;

-- Verify the data
SELECT
    'Applications' AS asset_type,
    COUNT(*) AS asset_count
FROM migration.assets
WHERE client_account_id = '11111111-1111-1111-1111-111111111111'::UUID
  AND engagement_id = '22222222-2222-2222-2222-222222222222'::UUID
  AND asset_type = 'application'
  AND name LIKE 'Test-%'
UNION ALL
SELECT
    'Non-application assets' AS asset_type,
    COUNT(*) AS asset_count
FROM migration.assets
WHERE client_account_id = '11111111-1111-1111-1111-111111111111'::UUID
  AND engagement_id = '22222222-2222-2222-2222-222222222222'::UUID
  AND asset_type != 'application'
  AND name LIKE 'Test-%'
UNION ALL
SELECT
    'Mapped non-app assets' AS asset_type,
    COUNT(*) AS asset_count
FROM migration.assets a
INNER JOIN migration.collection_flow_applications cfa ON a.id = cfa.asset_id
WHERE a.client_account_id = '11111111-1111-1111-1111-111111111111'::UUID
  AND a.engagement_id = '22222222-2222-2222-2222-222222222222'::UUID
  AND a.asset_type != 'application'
  AND a.name LIKE 'Test-%';
