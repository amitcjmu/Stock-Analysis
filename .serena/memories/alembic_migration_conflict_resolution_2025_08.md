# Alembic Migration Conflict Resolution - August 2025

## Problem Summary
The backend was failing to start with the error:
```
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head'
```

## Root Cause Analysis
The issue occurred because there were two divergent migration heads:
1. `017_add_asset_id_to_questionnaire_responses` - Added asset_id foreign key to questionnaire responses
2. `1687c833bfcc` - A merge migration that combined previous heads

Both branches stemmed from migration `016_add_security_constraints`, creating a branching conflict that Alembic couldn't automatically resolve.

## Solution Applied
1. **Identified the conflicting heads** using `alembic heads`:
   - `017_add_asset_id_to_questionnaire_responses` (head)
   - `1687c833bfcc` (head)

2. **Created a merge migration** using:
   ```bash
   python -m alembic merge -m "merge_heads_fix_questionnaire_asset_linkage" 017_add_asset_id_to_questionnaire_responses 1687c833bfcc
   ```

   This generated migration file: `cef530e273d4_merge_heads_fix_questionnaire_asset_.py`

3. **Applied the merge migration** using:
   ```bash
   POSTGRES_HOST=localhost POSTGRES_PORT=5433 python -m alembic upgrade head
   ```

4. **Verified the resolution** confirmed single head: `cef530e273d4`

## Key Technical Details
- **Database Connection**: Required environment variables `POSTGRES_HOST=localhost POSTGRES_PORT=5433` to connect to the Docker database
- **Migration Path**: The database was already at one head (`1687c833bfcc`) and needed to apply the other path first
- **Merge Migration**: Empty upgrade/downgrade functions since this was purely a path merge, no schema changes needed

## Files Modified
- `/backend/alembic/versions/cef530e273d4_merge_heads_fix_questionnaire_asset_.py` (created)

## Verification Steps
1. `alembic heads` shows single head: `cef530e273d4 (head)`
2. `alembic current` confirms database at merged head
3. `alembic history --verbose` shows proper merge structure
4. Migration chain is now linear and conflict-free

## Prevention
- When creating migrations on different branches, coordinate merge timing
- Use `alembic heads` to check for conflicts before deployment
- Consider using branch labels for long-running feature branches

The multiple heads issue is now completely resolved and the database migration system is working correctly.
