#!/bin/bash
# Verify LLM Usage Tracking is Working
# Run this after starting a discovery/assessment flow to verify logs are being recorded

echo "🔍 Checking LLM Usage Tracking..."
echo ""

# Check last 5 LLM log entries
echo "📊 Last 5 LLM usage log entries:"
docker exec migration_postgres psql -U postgres -d migration_db -c "
SELECT
    created_at,
    llm_provider,
    model_name,
    input_tokens,
    output_tokens,
    feature_context
FROM migration.llm_usage_logs
ORDER BY created_at DESC
LIMIT 5;
"

echo ""
echo "📈 Total LLM logs and date range:"
docker exec migration_postgres psql -U postgres -d migration_db -c "
SELECT
    COUNT(*) as total_logs,
    MIN(created_at) as earliest,
    MAX(created_at) as latest,
    EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at)))/3600 as hours_span
FROM migration.llm_usage_logs;
"

echo ""
echo "🎯 Logs in last 24 hours:"
docker exec migration_postgres psql -U postgres -d migration_db -c "
SELECT COUNT(*) as logs_last_24h
FROM migration.llm_usage_logs
WHERE created_at > NOW() - INTERVAL '24 hours';
"

echo ""
echo "💡 If logs_last_24h is 0, run a discovery/assessment flow to test tracking"
