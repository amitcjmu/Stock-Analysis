# Security Update Instructions

## Dependencies Updated

This branch contains security updates for the following vulnerable dependencies:

### Python Dependencies (Updated in requirements files)
- **starlette**: Updated to 0.47.2 (from various versions < 0.47.2)
  - Fixes security vulnerability in versions < 0.47.2
  - Already updated in all requirements*.txt files

- **fastapi**: Updated to 0.116.1 (from 0.115.14 and 0.116.0)
  - Required to support Starlette 0.47.2
  - FastAPI 0.116.1 supports Starlette >=0.40.0,<0.48.0

- **aiohttp**: Already at 3.12.14 (no update needed)
  - Was already at the patched version

### NPM Dependencies (Transitive - will update on rebuild)
- **@eslint/plugin-kit**: Needs >= 0.3.3 (currently < 0.3.3)
  - This is a transitive dependency of eslint
  - Will be updated when Docker containers are rebuilt

- **form-data**: Needs >= 4.0.4 (currently >= 4.0.0, < 4.0.4)
  - This is a transitive dependency of axios
  - Will be updated when Docker containers are rebuilt

## Steps to Apply Updates

1. **Merge this PR to main branch**

2. **Rebuild Docker containers to apply all updates:**
   ```bash
   # Stop existing containers
   docker-compose down

   # Rebuild containers with updated dependencies
   docker-compose build --no-cache

   # Start the application
   docker-compose up -d
   ```

3. **Verify updates were applied:**
   ```bash
   # Check Python packages in backend container
   docker-compose exec backend pip show starlette aiohttp

   # Check NPM packages in frontend container
   docker-compose exec frontend npm ls @eslint/plugin-kit form-data
   ```

## Notes

- The NPM packages (@eslint/plugin-kit and form-data) are transitive dependencies, not direct dependencies
- They will be automatically updated to secure versions when npm install runs during container rebuild
- All Python dependency updates have been applied to all requirements files to ensure consistency

## Testing

After rebuilding containers, please test:
1. Backend API functionality
2. Frontend build process
3. ESLint functionality
4. File upload features (uses form-data)
