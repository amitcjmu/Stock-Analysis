#!/bin/bash

# Verification script for MCQ questionnaire format
# Usage: ./verify_mcq_questionnaire.sh <flow_id>

if [ -z "$1" ]; then
    echo "Usage: $0 <flow_id>"
    echo "Example: $0 b7ba1f33-c463-4962-9c0b-6295effd224b"
    exit 1
fi

FLOW_ID=$1

echo "═══════════════════════════════════════════════════════════════"
echo "  Verifying MCQ Questionnaire Format for Flow: $FLOW_ID"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Get questionnaire details
docker exec migration_postgres psql -U postgres -d migration_db << EOF

-- 1. Get questionnaire basic info
SELECT
    '═══════════════════════════════════════════════════════════════' as separator,
    'QUESTIONNAIRE DETAILS' as section;

SELECT
    id as questionnaire_id,
    template_name,
    template_type,
    jsonb_array_length(questions) as total_questions,
    created_at
FROM migration.adaptive_questionnaires
WHERE collection_flow_id = '$FLOW_ID';

-- 2. Question type distribution
SELECT
    '═══════════════════════════════════════════════════════════════' as separator,
    'QUESTION TYPE DISTRIBUTION' as section;

SELECT
    q->>'field_type' as field_type,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM migration.adaptive_questionnaires,
    jsonb_array_elements(questions) as q
WHERE collection_flow_id = '$FLOW_ID'
GROUP BY q->>'field_type'
ORDER BY count DESC;

-- 3. MCQ vs Non-MCQ breakdown
SELECT
    '═══════════════════════════════════════════════════════════════' as separator,
    'MCQ FORMAT VERIFICATION' as section;

SELECT
    COUNT(CASE WHEN q->>'field_type' IN ('select', 'multiselect', 'radio') THEN 1 END) as mcq_questions,
    COUNT(CASE WHEN q->>'field_type' NOT IN ('select', 'multiselect', 'radio') THEN 1 END) as non_mcq_questions,
    COUNT(*) as total,
    ROUND(100.0 * COUNT(CASE WHEN q->>'field_type' IN ('select', 'multiselect', 'radio') THEN 1 END) / COUNT(*), 2) as mcq_percentage
FROM migration.adaptive_questionnaires,
    jsonb_array_elements(questions) as q
WHERE collection_flow_id = '$FLOW_ID';

-- 4. Question 5 details
SELECT
    '═══════════════════════════════════════════════════════════════' as separator,
    'QUESTION 5 DETAILS' as section;

SELECT
    questions->4->>'field_id' as field_id,
    questions->4->>'question_text' as question_text,
    questions->4->>'field_type' as field_type,
    questions->4->>'category' as category,
    jsonb_array_length(questions->4->'options') as option_count
FROM migration.adaptive_questionnaires
WHERE collection_flow_id = '$FLOW_ID';

-- 5. Category distribution
SELECT
    '═══════════════════════════════════════════════════════════════' as separator,
    'QUESTION CATEGORIES' as section;

SELECT
    q->>'category' as category,
    COUNT(*) as question_count
FROM migration.adaptive_questionnaires,
    jsonb_array_elements(questions) as q
WHERE collection_flow_id = '$FLOW_ID'
GROUP BY q->>'category'
ORDER BY question_count DESC;

EOF

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Verification Complete"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Expected Results for MCQ Format:"
echo "  ✓ MCQ percentage should be close to 100%"
echo "  ✓ field_type should be: select, multiselect, or radio"
echo "  ✓ Question 5 should have field_type = 'select' or 'multiselect'"
echo "  ✓ All questions should have option_count > 0"
echo ""
