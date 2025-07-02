#!/bin/bash

# Fix Hardcoded Demo IDs Script
# This script replaces hardcoded placeholder IDs with actual demo IDs from the database

echo "🔧 Fixing hardcoded demo IDs in frontend and backend..."

# Define the ID mappings
OLD_CLIENT_ID="11111111-1111-1111-1111-111111111111"
NEW_CLIENT_ID="4482c8d1-def0-def0-def0-957ab2b09d5c"

OLD_ENGAGEMENT_ID="22222222-2222-2222-2222-222222222222"
NEW_ENGAGEMENT_ID="9089bd69-def0-def0-def0-bda38c17d1a2"

# Frontend files
echo "📁 Updating frontend files..."

# Update TypeScript/React files
find src/ -type f \( -name "*.ts" -o -name "*.tsx" \) -exec grep -l "$OLD_CLIENT_ID" {} \; | while read file; do
    echo "  Updating $file (client ID)..."
    sed -i.bak "s/$OLD_CLIENT_ID/$NEW_CLIENT_ID/g" "$file"
done

find src/ -type f \( -name "*.ts" -o -name "*.tsx" \) -exec grep -l "$OLD_ENGAGEMENT_ID" {} \; | while read file; do
    echo "  Updating $file (engagement ID)..."
    sed -i.bak "s/$OLD_ENGAGEMENT_ID/$NEW_ENGAGEMENT_ID/g" "$file"
done

# Backend files
echo "📁 Updating backend files..."

# Update Python files
find backend/ -type f -name "*.py" -exec grep -l "$OLD_CLIENT_ID" {} \; | while read file; do
    echo "  Updating $file (client ID)..."
    sed -i.bak "s/$OLD_CLIENT_ID/$NEW_CLIENT_ID/g" "$file"
done

find backend/ -type f -name "*.py" -exec grep -l "$OLD_ENGAGEMENT_ID" {} \; | while read file; do
    echo "  Updating $file (engagement ID)..."
    sed -i.bak "s/$OLD_ENGAGEMENT_ID/$NEW_ENGAGEMENT_ID/g" "$file"
done

# Update platform admin defaults in database
echo "🗄️ Updating platform admin defaults..."
docker exec -it migration_postgres psql -U postgres -d migration_db -c "
UPDATE user_profiles 
SET default_client_id = '$NEW_CLIENT_ID'::uuid,
    default_engagement_id = '$NEW_ENGAGEMENT_ID'::uuid
WHERE email = 'chocka@gmail.com';
"

# Clean up backup files
echo "🧹 Cleaning up backup files..."
find . -name "*.bak" -type f -delete

echo "✅ Done! Hardcoded IDs have been updated."
echo ""
echo "📋 Summary of changes:"
echo "  Client ID:     $OLD_CLIENT_ID → $NEW_CLIENT_ID"
echo "  Engagement ID: $OLD_ENGAGEMENT_ID → $NEW_ENGAGEMENT_ID"
echo ""
echo "🔄 Next steps:"
echo "  1. Restart the frontend: docker-compose restart frontend"
echo "  2. Clear browser cache and localStorage"
echo "  3. Login again and test file upload"