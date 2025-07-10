# Issue Summary: Context Mismatch Causing File Upload Failures

## The Problem
File upload and Discovery flow initiation are failing due to a **simple but critical mismatch** between hardcoded demo IDs in the code and actual IDs in the database.

## Root Cause

### What's Happening:
1. **Frontend sends wrong IDs**: The browser is sending hardcoded placeholder IDs that don't exist
2. **Backend rejects them**: Database foreign key constraints reject these non-existent IDs
3. **No fallback to real IDs**: System doesn't detect and correct the invalid IDs

### The Mismatch:
```
Code Uses (Hardcoded):          Database Has (Real):
Client:     11111111-1111-...   →   4482c8d1-def0-def0-def0-957ab2b09d5c
Engagement: 22222222-2222-...   →   9089bd69-def0-def0-def0-bda38c17d1a2
```

## Why This Happened

1. **Development Evolution**:
   - Early development used simple placeholder IDs (11111111...)
   - Database seeding scripts created proper demo data with real UUIDs
   - Frontend code was never updated to use the real IDs

2. **Missing Context Flow**:
   - After login, system should load user's clients/engagements
   - Platform admin has no defaults set
   - System falls back to hardcoded (wrong) IDs instead of prompting

3. **No Validation**:
   - Frontend doesn't verify IDs exist before using them
   - Backend only catches issue at database constraint level

## Impact

- ❌ File uploads fail with foreign key errors
- ❌ Discovery flows can't be created
- ❌ API calls include invalid context headers
- ✅ Everything else works fine (the actual functionality is correct)

## The Solution

### Quick Fix (Provided):
Run the `fix_hardcoded_ids.sh` script to:
1. Replace all hardcoded IDs with real ones
2. Update platform admin's default client/engagement
3. Restart services

### Proper Fix (Recommended):
1. Remove ALL hardcoded IDs
2. Implement proper context selection after login
3. Add validation before sending API requests
4. Use environment variables for demo data

## Verification

After applying the fix:
1. Browser will send correct headers:
   ```
   X-Client-Account-ID: 4482c8d1-def0-def0-def0-957ab2b09d5c
   X-Engagement-ID: 9089bd69-def0-def0-def0-bda38c17d1a2
   ```
2. File uploads will succeed
3. Discovery flows will be created properly

## Key Insight

**The Discovery flow and file upload features are working perfectly**. The only issue is that they're being given invalid reference IDs. Once the correct IDs are used, everything functions as designed.

This is a configuration issue, not a functional bug.