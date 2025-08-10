-- Collection Flow Diagnostic Queries
-- Run these queries to understand the current state of collection flows

-- 1. Show all collection flows with their statuses
SELECT
    id,
    engagement_id,
    status,
    current_phase,
    automation_tier,
    progress_percentage,
    created_at,
    updated_at,
    completed_at,
    EXTRACT(EPOCH FROM (NOW() - created_at))/3600 as hours_since_created,
    EXTRACT(EPOCH FROM (NOW() - updated_at))/3600 as hours_since_updated
FROM collection_flow
ORDER BY created_at DESC;

-- 2. Show only ACTIVE flows (non-terminal states)
SELECT
    id,
    engagement_id,
    status,
    current_phase,
    progress_percentage,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - updated_at))/3600 as hours_since_updated
FROM collection_flow
WHERE status NOT IN ('completed', 'failed', 'cancelled')
ORDER BY created_at DESC;

-- 3. Count flows by status
SELECT
    status,
    COUNT(*) as count
FROM collection_flow
GROUP BY status
ORDER BY status;

-- 4. Show active flows grouped by engagement
SELECT
    engagement_id,
    COUNT(*) as active_flow_count,
    STRING_AGG(id::text || ' (' || status || ')', ', ') as flow_details
FROM collection_flow
WHERE status NOT IN ('completed', 'failed', 'cancelled')
GROUP BY engagement_id;

-- 5. Find stuck flows (active but not updated in 24 hours)
SELECT
    id,
    engagement_id,
    status,
    current_phase,
    created_at,
    updated_at,
    EXTRACT(EPOCH FROM (NOW() - updated_at))/3600 as hours_stuck
FROM collection_flow
WHERE status NOT IN ('completed', 'failed', 'cancelled')
    AND updated_at < NOW() - INTERVAL '24 hours'
ORDER BY updated_at;

-- 6. Cancel all stuck flows (COMMENTED OUT FOR SAFETY - uncomment to run)
-- UPDATE collection_flow
-- SET status = 'cancelled',
--     completed_at = NOW(),
--     updated_at = NOW()
-- WHERE status NOT IN ('completed', 'failed', 'cancelled')
--     AND updated_at < NOW() - INTERVAL '24 hours';

-- 7. Show the test engagement ID we're using (bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb)
SELECT
    id,
    engagement_id,
    status,
    current_phase,
    created_at,
    updated_at
FROM collection_flow
WHERE engagement_id = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
ORDER BY created_at DESC;
