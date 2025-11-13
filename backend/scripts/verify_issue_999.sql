-- Verification Query for Issue #999: Assets Table Update with 6R Strategies
-- This query verifies that 6R strategies are populated in the assets table after assessment

-- Check 1: Count assets with 6R strategies
SELECT
    COUNT(*) as total_assets,
    COUNT(CASE WHEN six_r_strategy IS NOT NULL THEN 1 END) as assets_with_6r,
    COUNT(CASE WHEN confidence_score IS NOT NULL THEN 1 END) as assets_with_confidence,
    COUNT(CASE WHEN assessment_flow_id IS NOT NULL THEN 1 END) as assets_with_assessment_flow
FROM migration.assets
WHERE deleted_at IS NULL;

-- Check 2: Distribution of 6R strategies
SELECT
    six_r_strategy,
    COUNT(*) as count,
    AVG(confidence_score) as avg_confidence,
    MIN(confidence_score) as min_confidence,
    MAX(confidence_score) as max_confidence
FROM migration.assets
WHERE six_r_strategy IS NOT NULL
  AND deleted_at IS NULL
GROUP BY six_r_strategy
ORDER BY count DESC;

-- Check 3: Recent updates with 6R strategies
SELECT
    id,
    name,
    application_name,
    six_r_strategy,
    ROUND(confidence_score::numeric, 2) as confidence_score,
    assessment_flow_id,
    updated_at
FROM migration.assets
WHERE six_r_strategy IS NOT NULL
  AND deleted_at IS NULL
ORDER BY updated_at DESC
LIMIT 10;

-- Check 4: Assets by application with 6R strategies
SELECT
    application_name,
    COUNT(*) as asset_count,
    six_r_strategy,
    AVG(confidence_score) as avg_confidence
FROM migration.assets
WHERE application_name IS NOT NULL
  AND six_r_strategy IS NOT NULL
  AND deleted_at IS NULL
GROUP BY application_name, six_r_strategy
ORDER BY asset_count DESC
LIMIT 15;

-- Check 5: Assessment flows and their asset counts
SELECT
    af.id as assessment_flow_id,
    af.flow_name,
    af.current_phase,
    af.status,
    COUNT(DISTINCT a.id) as assets_updated_count,
    COUNT(DISTINCT a.application_name) as unique_applications
FROM migration.assessment_flows af
LEFT JOIN migration.assets a ON a.assessment_flow_id = af.id
WHERE a.six_r_strategy IS NOT NULL
  AND a.deleted_at IS NULL
GROUP BY af.id, af.flow_name, af.current_phase, af.status
ORDER BY af.created_at DESC
LIMIT 5;
