# Fix: "Google Generative AI SDK not available" Warning

## Problem
You're seeing this warning:
```
WARNING - Google Generative AI SDK not available for Gemini.
```

This means the `google-generativeai` package is not installed in the Python environment where your backend is running.

## Solution

### If Running in Docker (Most Common)

Your backend is running in a Docker container (`migration_backend`). You have two options:

#### Option 1: Install in Running Container (Quick Fix)
```bash
# Install the package in the running container
docker exec -it migration_backend pip install google-generativeai==0.8.3

# Restart the container to ensure it's loaded
docker restart migration_backend
```

#### Option 2: Rebuild Container (Recommended for Production)
```bash
# Stop the container
docker stop migration_backend

# Rebuild with updated requirements
cd /Users/amitchoudhary/Desktop/Stock-Analysis-project
docker-compose -f config/docker/docker-compose.dev.yml build backend

# Or if using production compose:
# docker-compose -f config/docker/docker-compose.prod.yml build backend

# Start the container
docker-compose -f config/docker/docker-compose.dev.yml up -d backend
```

**Note:** The package has already been added to `requirements-docker.txt`, so rebuilding will include it.

### If Running Locally (Not Docker)

#### Check for Virtual Environment
```bash
cd backend

# If you have a venv
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install google-generativeai==0.8.3
else
    # Install in your Python environment
    pip3 install google-generativeai==0.8.3
fi
```

#### Verify Installation
```bash
python3 -c "import google.generativeai as genai; print('✅ SDK available')"
```

### Verify the Fix

After installing, restart your backend and check the logs. You should see:
```
✅ Initialized Google Gemini client for gemini-1.5-pro
```

Instead of the warning.

## Quick Docker Fix Command

Run this single command to fix it immediately:

```bash
docker exec migration_backend pip install google-generativeai==0.8.3 && docker restart migration_backend
```

## Still Having Issues?

1. **Check which Python the backend is using:**
   ```bash
   docker exec migration_backend which python3
   docker exec migration_backend python3 --version
   ```

2. **Check if package is installed:**
   ```bash
   docker exec migration_backend pip list | grep google-generativeai
   ```

3. **Check backend logs:**
   ```bash
   docker logs migration_backend | grep -i gemini
   ```

4. **Verify environment variable is set:**
   ```bash
   docker exec migration_backend env | grep GOOGLE_GEMINI_API_KEY
   ```

## Next Steps

After fixing the package installation:
1. Set the `GOOGLE_GEMINI_API_KEY` environment variable (see `GEMINI_SETUP.md`)
2. Restart the backend
3. Test by selecting "Google Gemini" from the model dropdown in the UI
