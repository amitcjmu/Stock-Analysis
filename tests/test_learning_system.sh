#!/bin/bash

echo "🎯 Testing AI Learning System in Docker Environment"
echo "=================================================="

# Function to test API endpoints
test_endpoint() {
    local endpoint=$1
    local method=$2
    local data=$3
    local description=$4

    echo "🧪 Testing: $description"
    echo "   Endpoint: $method $endpoint"

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" "http://localhost:8000$endpoint")
    else
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "http://localhost:8000$endpoint")
    fi

    http_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]*$//')

    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
        echo "   ✅ SUCCESS ($http_code)"
        echo "$body" | python -m json.tool 2>/dev/null | head -10
    else
        echo "   ❌ FAILED ($http_code)"
        echo "   Response: $body"
    fi
    echo ""
}

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# 1. Test Learning Statistics (should start empty)
test_endpoint "/api/v1/data_import/learning-statistics" "GET" "" "Initial Learning Statistics"

# 2. Test Dynamic Field Creation
echo "🔧 Creating Custom Field: 'mac_address'"
test_endpoint "/api/v1/data_import/custom-fields" "POST" '{
    "field_name": "mac_address",
    "field_type": "string",
    "description": "MAC address for network identification",
    "required": false,
    "is_critical": false
}' "Create MAC Address Field"

# 3. Test Another Custom Field
echo "🔧 Creating Custom Field: 'related_cmdb_records'"
test_endpoint "/api/v1/data_import/custom-fields" "POST" '{
    "field_name": "related_cmdb_records",
    "field_type": "string",
    "description": "Related CMDB record references",
    "required": false,
    "is_critical": false
}' "Create Related CMDB Records Field"

# 4. Test Field Mapping Suggestions (should now include custom fields)
test_endpoint "/api/v1/data_import/imports/2dc83ab7-1609-4ddc-a13a-d170767cf76f/field-mapping-suggestions" "GET" "" "Field Mapping Suggestions with Custom Fields"

# 5. Test AI Learning from User Correction
echo "🧠 Teaching AI: 'ID' maps to 'hostname'"
test_endpoint "/api/v1/data_import/imports/2dc83ab7-1609-4ddc-a13a-d170767cf76f/learn-from-mapping" "POST" '{
    "source_field": "ID",
    "corrected_target_field": "hostname",
    "original_suggestion": "asset_name",
    "sample_values": ["SRV001", "SRV002", "SRV003"],
    "was_correct": true,
    "feedback": "ID fields contain server hostnames, not application names",
    "reason": "Semantic correction: IDs are hostnames"
}' "Learn: ID → hostname"

# 6. Test AI Learning from Another Correction
echo "🧠 Teaching AI: 'NAME' maps to 'asset_name'"
test_endpoint "/api/v1/data_import/imports/2dc83ab7-1609-4ddc-a13a-d170767cf76f/learn-from-mapping" "POST" '{
    "source_field": "NAME",
    "corrected_target_field": "asset_name",
    "original_suggestion": "hostname",
    "sample_values": ["Web_Server_01", "DB_Primary", "API_Gateway"],
    "was_correct": true,
    "feedback": "NAME fields contain descriptive application names",
    "reason": "Semantic correction: NAMEs are asset names"
}' "Learn: NAME → asset_name"

# 7. Test Learning for Custom Field
echo "🧠 Teaching AI: 'RELATED CMDB RECORDS' maps to custom field"
test_endpoint "/api/v1/data_import/imports/2dc83ab7-1609-4ddc-a13a-d170767cf76f/learn-from-mapping" "POST" '{
    "source_field": "RELATED CMDB RECORDS",
    "corrected_target_field": "related_cmdb_records",
    "sample_values": ["", "SRV001", "SRV001;SRV003"],
    "was_correct": true,
    "is_custom_field": true,
    "feedback": "This field maps to our custom related records field",
    "reason": "Custom field mapping learned"
}' "Learn: RELATED CMDB RECORDS → related_cmdb_records"

# 8. Test Updated Learning Statistics
echo "📊 Checking Learning Progress..."
test_endpoint "/api/v1/data_import/learning-statistics" "GET" "" "Updated Learning Statistics"

# 9. Test Field Suggestions Again (should be improved)
echo "🎯 Testing Improved AI Suggestions..."
test_endpoint "/api/v1/data_import/imports/2dc83ab7-1609-4ddc-a13a-d170767cf76f/field-mapping-suggestions" "GET" "" "Improved Field Mapping Suggestions"

# 10. Test Available Fields (should include custom fields)
test_endpoint "/api/v1/data_import/available-target-fields" "GET" "" "Available Target Fields (with custom fields)"

echo "🎉 Learning System Test Complete!"
echo ""
echo "🧠 What the AI Should Have Learned:"
echo "   • ID → hostname (server identifiers)"
echo "   • NAME → asset_name (descriptive names)"
echo "   • RELATED CMDB RECORDS → related_cmdb_records (custom field)"
echo "   • Created 2 custom fields: mac_address, related_cmdb_records"
echo ""
echo "🔮 Next Time You Upload Similar Data:"
echo "   • AI will automatically suggest these mappings"
echo "   • Custom fields will be available in dropdown"
echo "   • System gets smarter with each correction"
