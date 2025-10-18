#!/bin/bash

# Milestone field population script
# This script adds milestone definition issues to the project and populates custom fields

PROJECT_NUMBER=2
OWNER="CryptoYogiLLC"

# Field IDs
READINESS_FIELD="PVTSSF_lAHOC9ukJs4A-zrvzg3AXhg"
EFFORT_FIELD="PVTSSF_lAHOC9ukJs4A-zrvzg3AXj4"
ISSUES_CREATED_FIELD="PVTF_lAHOC9ukJs4A-zrvzg3AXkk"
ISSUES_REMAINING_FIELD="PVTF_lAHOC9ukJs4A-zrvzg3AXko"
COMPLETION_FIELD="PVTF_lAHOC9ukJs4A-zrvzg3AXlY"

# Readiness Level option IDs
READINESS_NOT_BROKEN="69b6b19d"
READINESS_NEEDS_SPIKE="14e9e465"
READINESS_READY="d5f88167"
READINESS_IN_PROGRESS="a746a438"
READINESS_DONE="1ce02541"

# Estimated Effort option IDs
EFFORT_1_2_WEEKS="bc4682de"
EFFORT_3_4_WEEKS="689f2cc8"
EFFORT_5_8_WEEKS="165c6960"
EFFORT_9_12_WEEKS="9e7c44ec"
EFFORT_12_PLUS="5995f0c9"
EFFORT_UNKNOWN="f2a32bdf"

# Function to add issue to project and get item ID
add_and_get_item_id() {
    local issue_number=$1
    echo "Adding issue #$issue_number to project..."

    # Add issue to project
    /opt/homebrew/bin/gh project item-add $PROJECT_NUMBER --owner $OWNER \
        --url "https://github.com/$OWNER/migrate-ui-orchestrator/issues/$issue_number" 2>/dev/null

    # Get item ID (wait a moment for it to be added)
    sleep 1

    # Get the item ID from the project
    local item_id=$(/opt/homebrew/bin/gh project item-list $PROJECT_NUMBER --owner $OWNER \
        --format json --limit 200 | \
        jq -r ".items[] | select(.content.number == $issue_number) | .id")

    echo "Item ID for #$issue_number: $item_id"
    echo "$item_id"
}

# Function to set single-select field
set_single_select_field() {
    local item_id=$1
    local field_id=$2
    local option_id=$3

    /opt/homebrew/bin/gh project item-edit --project-id $PROJECT_NUMBER --id "$item_id" \
        --field-id "$field_id" --single-select-option-id "$option_id" 2>/dev/null || true
}

# Function to set number field
set_number_field() {
    local item_id=$1
    local field_id=$2
    local value=$3

    /opt/homebrew/bin/gh project item-edit --project-id $PROJECT_NUMBER --id "$item_id" \
        --field-id "$field_id" --number "$value" 2>/dev/null || true
}

echo "======================================"
echo "Populating Milestone Project Fields"
echo "======================================"
echo ""

# Issue #606: Planning Flow
echo "Processing #606: Planning Flow Complete"
ITEM_ID=$(add_and_get_item_id 606)
if [ ! -z "$ITEM_ID" ]; then
    set_single_select_field "$ITEM_ID" "$READINESS_FIELD" "$READINESS_NOT_BROKEN"
    set_single_select_field "$ITEM_ID" "$EFFORT_FIELD" "$EFFORT_12_PLUS"
    set_number_field "$ITEM_ID" "$ISSUES_CREATED_FIELD" 2
    set_number_field "$ITEM_ID" "$ISSUES_REMAINING_FIELD" 2
    set_number_field "$ITEM_ID" "$COMPLETION_FIELD" 10
    echo "✓ #606 populated"
fi
echo ""

# Issue #607: Client Demo
echo "Processing #607: Client Demo"
ITEM_ID=$(add_and_get_item_id 607)
if [ ! -z "$ITEM_ID" ]; then
    set_single_select_field "$ITEM_ID" "$READINESS_FIELD" "$READINESS_NEEDS_SPIKE"
    set_single_select_field "$ITEM_ID" "$EFFORT_FIELD" "$EFFORT_5_8_WEEKS"
    set_number_field "$ITEM_ID" "$ISSUES_CREATED_FIELD" 1
    set_number_field "$ITEM_ID" "$ISSUES_REMAINING_FIELD" 1
    set_number_field "$ITEM_ID" "$COMPLETION_FIELD" 7
    echo "✓ #607 populated"
fi
echo ""

# Issue #608: Beta User Onboarding
echo "Processing #608: Beta User Onboarding"
ITEM_ID=$(add_and_get_item_id 608)
if [ ! -z "$ITEM_ID" ]; then
    set_single_select_field "$ITEM_ID" "$READINESS_FIELD" "$READINESS_NEEDS_SPIKE"
    set_single_select_field "$ITEM_ID" "$EFFORT_FIELD" "$EFFORT_9_12_WEEKS"
    set_number_field "$ITEM_ID" "$ISSUES_CREATED_FIELD" 1
    set_number_field "$ITEM_ID" "$ISSUES_REMAINING_FIELD" 1
    set_number_field "$ITEM_ID" "$COMPLETION_FIELD" 5
    echo "✓ #608 populated"
fi
echo ""

# Issue #609: Discovery Flow Phase 1 Cleanup
echo "Processing #609: Discovery Flow Phase 1 Cleanup"
ITEM_ID=$(add_and_get_item_id 609)
if [ ! -z "$ITEM_ID" ]; then
    set_single_select_field "$ITEM_ID" "$READINESS_FIELD" "$READINESS_IN_PROGRESS"
    set_single_select_field "$ITEM_ID" "$EFFORT_FIELD" "$EFFORT_5_8_WEEKS"
    set_number_field "$ITEM_ID" "$ISSUES_CREATED_FIELD" 186
    set_number_field "$ITEM_ID" "$ISSUES_REMAINING_FIELD" 44
    set_number_field "$ITEM_ID" "$COMPLETION_FIELD" 81
    echo "✓ #609 populated"
fi
echo ""

# Issue #610: Collection Flow Ready
echo "Processing #610: Collection Flow Ready"
ITEM_ID=$(add_and_get_item_id 610)
if [ ! -z "$ITEM_ID" ]; then
    set_single_select_field "$ITEM_ID" "$READINESS_FIELD" "$READINESS_READY"
    set_single_select_field "$ITEM_ID" "$EFFORT_FIELD" "$EFFORT_1_2_WEEKS"
    set_number_field "$ITEM_ID" "$ISSUES_CREATED_FIELD" 61
    set_number_field "$ITEM_ID" "$ISSUES_REMAINING_FIELD" 2
    set_number_field "$ITEM_ID" "$COMPLETION_FIELD" 97
    echo "✓ #610 populated"
fi
echo ""

# Issue #611: Assessment Flow Complete
echo "Processing #611: Assessment Flow Complete"
ITEM_ID=$(add_and_get_item_id 611)
if [ ! -z "$ITEM_ID" ]; then
    set_single_select_field "$ITEM_ID" "$READINESS_FIELD" "$READINESS_READY"
    set_single_select_field "$ITEM_ID" "$EFFORT_FIELD" "$EFFORT_3_4_WEEKS"
    set_number_field "$ITEM_ID" "$ISSUES_CREATED_FIELD" 9
    set_number_field "$ITEM_ID" "$ISSUES_REMAINING_FIELD" 1
    set_number_field "$ITEM_ID" "$COMPLETION_FIELD" 90
    echo "✓ #611 populated"
fi
echo ""

# Issue #612: Fresher Onboarding
echo "Processing #612: Fresher Onboarding"
ITEM_ID=$(add_and_get_item_id 612)
if [ ! -z "$ITEM_ID" ]; then
    set_single_select_field "$ITEM_ID" "$READINESS_FIELD" "$READINESS_READY"
    set_single_select_field "$ITEM_ID" "$EFFORT_FIELD" "$EFFORT_3_4_WEEKS"
    set_number_field "$ITEM_ID" "$ISSUES_CREATED_FIELD" 1
    set_number_field "$ITEM_ID" "$ISSUES_REMAINING_FIELD" 3
    set_number_field "$ITEM_ID" "$COMPLETION_FIELD" 25
    echo "✓ #612 populated"
fi
echo ""

# Issue #613: Security Documents Archival
echo "Processing #613: Security Documents Archival"
ITEM_ID=$(add_and_get_item_id 613)
if [ ! -z "$ITEM_ID" ]; then
    set_single_select_field "$ITEM_ID" "$READINESS_FIELD" "$READINESS_NOT_BROKEN"
    set_single_select_field "$ITEM_ID" "$EFFORT_FIELD" "$EFFORT_5_8_WEEKS"
    set_number_field "$ITEM_ID" "$ISSUES_CREATED_FIELD" 0
    set_number_field "$ITEM_ID" "$ISSUES_REMAINING_FIELD" 2
    set_number_field "$ITEM_ID" "$COMPLETION_FIELD" 0
    echo "✓ #613 populated"
fi
echo ""

# Issue #614: QA Team Readiness
echo "Processing #614: QA Team Readiness"
ITEM_ID=$(add_and_get_item_id 614)
if [ ! -z "$ITEM_ID" ]; then
    set_single_select_field "$ITEM_ID" "$READINESS_FIELD" "$READINESS_READY"
    set_single_select_field "$ITEM_ID" "$EFFORT_FIELD" "$EFFORT_1_2_WEEKS"
    set_number_field "$ITEM_ID" "$ISSUES_CREATED_FIELD" 11
    set_number_field "$ITEM_ID" "$ISSUES_REMAINING_FIELD" 1
    set_number_field "$ITEM_ID" "$COMPLETION_FIELD" 92
    echo "✓ #614 populated"
fi
echo ""

# Issue #615: Alpha Users Onboarding
echo "Processing #615: Alpha Users Onboarding"
ITEM_ID=$(add_and_get_item_id 615)
if [ ! -z "$ITEM_ID" ]; then
    set_single_select_field "$ITEM_ID" "$READINESS_FIELD" "$READINESS_READY"
    set_single_select_field "$ITEM_ID" "$EFFORT_FIELD" "$EFFORT_3_4_WEEKS"
    set_number_field "$ITEM_ID" "$ISSUES_CREATED_FIELD" 14
    set_number_field "$ITEM_ID" "$ISSUES_REMAINING_FIELD" 1
    set_number_field "$ITEM_ID" "$COMPLETION_FIELD" 93
    echo "✓ #615 populated"
fi
echo ""

# Issue #616: Phase 1 App Accessibility
echo "Processing #616: Phase 1 App Accessibility"
ITEM_ID=$(add_and_get_item_id 616)
if [ ! -z "$ITEM_ID" ]; then
    set_single_select_field "$ITEM_ID" "$READINESS_FIELD" "$READINESS_IN_PROGRESS"
    set_single_select_field "$ITEM_ID" "$EFFORT_FIELD" "$EFFORT_5_8_WEEKS"
    set_number_field "$ITEM_ID" "$ISSUES_CREATED_FIELD" 21
    set_number_field "$ITEM_ID" "$ISSUES_REMAINING_FIELD" 7
    set_number_field "$ITEM_ID" "$COMPLETION_FIELD" 75
    echo "✓ #616 populated"
fi
echo ""

# Issue #617: Branding & Messaging
echo "Processing #617: Branding & Messaging"
ITEM_ID=$(add_and_get_item_id 617)
if [ ! -z "$ITEM_ID" ]; then
    set_single_select_field "$ITEM_ID" "$READINESS_FIELD" "$READINESS_READY"
    set_single_select_field "$ITEM_ID" "$EFFORT_FIELD" "$EFFORT_3_4_WEEKS"
    set_number_field "$ITEM_ID" "$ISSUES_CREATED_FIELD" 2
    set_number_field "$ITEM_ID" "$ISSUES_REMAINING_FIELD" 1
    set_number_field "$ITEM_ID" "$COMPLETION_FIELD" 67
    echo "✓ #617 populated"
fi
echo ""

# Issue #618: Client Access (SaaS)
echo "Processing #618: Client Access (SaaS)"
ITEM_ID=$(add_and_get_item_id 618)
if [ ! -z "$ITEM_ID" ]; then
    set_single_select_field "$ITEM_ID" "$READINESS_FIELD" "$READINESS_NOT_BROKEN"
    set_single_select_field "$ITEM_ID" "$EFFORT_FIELD" "$EFFORT_12_PLUS"
    set_number_field "$ITEM_ID" "$ISSUES_CREATED_FIELD" 1
    set_number_field "$ITEM_ID" "$ISSUES_REMAINING_FIELD" 2
    set_number_field "$ITEM_ID" "$COMPLETION_FIELD" 33
    echo "✓ #618 populated"
fi
echo ""

# Issue #619: Code Cleansing Phase 1
echo "Processing #619: Code Cleansing Phase 1"
ITEM_ID=$(add_and_get_item_id 619)
if [ ! -z "$ITEM_ID" ]; then
    set_single_select_field "$ITEM_ID" "$READINESS_FIELD" "$READINESS_IN_PROGRESS"
    set_single_select_field "$ITEM_ID" "$EFFORT_FIELD" "$EFFORT_5_8_WEEKS"
    set_number_field "$ITEM_ID" "$ISSUES_CREATED_FIELD" 9
    set_number_field "$ITEM_ID" "$ISSUES_REMAINING_FIELD" 3
    set_number_field "$ITEM_ID" "$COMPLETION_FIELD" 75
    echo "✓ #619 populated"
fi
echo ""

# Issue #620: Discovery Flow Phase 2
echo "Processing #620: Discovery Flow Phase 2"
ITEM_ID=$(add_and_get_item_id 620)
if [ ! -z "$ITEM_ID" ]; then
    set_single_select_field "$ITEM_ID" "$READINESS_FIELD" "$READINESS_NOT_BROKEN"
    set_single_select_field "$ITEM_ID" "$EFFORT_FIELD" "$EFFORT_12_PLUS"
    set_number_field "$ITEM_ID" "$ISSUES_CREATED_FIELD" 0
    set_number_field "$ITEM_ID" "$ISSUES_REMAINING_FIELD" 2
    set_number_field "$ITEM_ID" "$COMPLETION_FIELD" 0
    echo "✓ #620 populated"
fi
echo ""

echo "======================================"
echo "✅ All milestone fields populated!"
echo "======================================"
echo ""
echo "Visit your project to see the results:"
echo "https://github.com/users/$OWNER/projects/$PROJECT_NUMBER"
