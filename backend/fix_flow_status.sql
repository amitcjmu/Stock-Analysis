-- Fix for flow 5d4149d3-ac32-40ea-85d1-56ebea8d5e17 stuck in failed state
-- This resets the flow status to allow proper data retrieval

-- Reset the CrewAI flow state to remove the "failed" status
UPDATE crewai_flow_state_extensions
SET flow_persistence_data = jsonb_set(
    COALESCE(flow_persistence_data, '{}'),
    '{status}',
    '"active"'
)
WHERE flow_id = '5d4149d3-ac32-40ea-85d1-56ebea8d5e17';

-- Ensure the discovery flow is marked as active
UPDATE discovery_flows
SET status = 'active'
WHERE flow_id = '5d4149d3-ac32-40ea-85d1-56ebea8d5e17';

-- Verify the fix
SELECT
    df.flow_id,
    df.status AS discovery_status,
    df.data_import_id,
    cfse.flow_persistence_data->>'status' AS crewai_status
FROM discovery_flows df
LEFT JOIN crewai_flow_state_extensions cfse ON df.flow_id = cfse.flow_id
WHERE df.flow_id = '5d4149d3-ac32-40ea-85d1-56ebea8d5e17';
