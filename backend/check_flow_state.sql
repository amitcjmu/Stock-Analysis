-- Check discovery_flows table (child - source of truth)
SELECT
    flow_id,
    status,
    progress_percentage,
    current_phase,
    crewai_state_data->>'status' as state_status,
    crewai_state_data->>'awaiting_user_approval' as awaiting_approval,
    updated_at
FROM discovery_flows
ORDER BY updated_at DESC
LIMIT 5;

-- Check master flow table
SELECT
    flow_id,
    flow_status,
    flow_persistence_data->>'status' as persistence_status,
    flow_persistence_data->>'awaiting_user_approval' as awaiting_approval,
    updated_at
FROM crewai_flow_state_extensions
WHERE flow_type = 'discovery'
ORDER BY updated_at DESC
LIMIT 5;
