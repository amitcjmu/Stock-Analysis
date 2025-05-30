# Environment Configuration Guide

## Overview

The AI Force Migration Platform uses environment variables to configure API endpoints and backend services for different deployment scenarios. This guide covers configuration for local development, Docker, and production deployments with Vercel (frontend) + Railway (backend).

## Environment Variables

### Frontend Variables (Vite)

All frontend environment variables must be prefixed with `VITE_` to be accessible in the browser.

#### Required Variables

| Variable | Description | Development | Production |
|----------|-------------|-------------|------------|
| `VITE_BACKEND_URL` | Backend API base URL | `http://localhost:8000` | `https://your-railway-app.railway.app` |
| `VITE_WS_BASE_URL` | WebSocket URL (optional) | `ws://localhost:8000/api/v1/ws` | `wss://your-railway-app.railway.app/api/v1/ws` |

#### Alternative Variable Names (for compatibility)

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE_URL` | Alternative to `VITE_BACKEND_URL` |
| `VITE_WS_URL` | Alternative to `VITE_WS_BASE_URL` |

### Backend Variables

See `backend/env.example` for complete backend configuration.

## Configuration by Environment

### 1. Local Development

Create `.env.local` in the project root:

```env
# Backend API Configuration
VITE_BACKEND_URL=http://localhost:8000

# WebSocket Configuration (optional)
VITE_WS_BASE_URL=ws://localhost:8000/api/v1/ws
```

### 2. Docker Development

The `docker-compose.yml` file automatically sets:

```yaml
environment:
  - VITE_BACKEND_URL=http://localhost:8000
  - VITE_WS_BASE_URL=ws://localhost:8000/api/v1/ws
```

### 3. Vercel + Railway Production

#### Vercel Configuration

In your Vercel project dashboard, set these environment variables:

```env
# Replace with your actual Railway app URL
VITE_BACKEND_URL=https://migrate-ui-orchestrator-production.up.railway.app
VITE_WS_BASE_URL=wss://migrate-ui-orchestrator-production.up.railway.app/api/v1/ws
```

#### Railway Configuration

Railway automatically provides the backend URL. Ensure your Railway app is properly configured with the backend environment variables from `backend/env.example`.

**Critical: Set CORS Environment Variable**

In your Railway project dashboard, set this environment variable to allow requests from Vercel:

```env
ALLOWED_ORIGINS=http://localhost:8081,http://localhost:3000,http://localhost:5173,https://aiforce-assess.vercel.app
```

**Important**: Replace `aiforce-assess.vercel.app` with your actual Vercel domain. FastAPI CORS middleware doesn't support wildcard patterns, so you need to specify each domain explicitly.

If you have multiple Vercel deployments (preview branches), add them individually:
```env
ALLOWED_ORIGINS=http://localhost:8081,https://aiforce-assess.vercel.app,https://aiforce-assess-git-main-yourname.vercel.app
```

Other important Railway environment variables:
- `DATABASE_URL` - Automatically provided by Railway
- `DEEPINFRA_API_KEY` - Your DeepInfra API key for AI features
- `SECRET_KEY` - Change the default secret key for security
- `ENVIRONMENT=production` - Set production mode

## How URL Resolution Works

### API Base URL Resolution Priority

1. `VITE_BACKEND_URL` environment variable
2. `VITE_API_BASE_URL` environment variable (fallback)
3. Development mode: `http://localhost:8000`
4. Production fallback: Same origin (with warning)

### WebSocket URL Resolution Priority

1. `VITE_WS_BASE_URL` environment variable
2. `VITE_WS_URL` environment variable (fallback)
3. Derived from `VITE_BACKEND_URL` (HTTP → WS conversion)
4. Development mode: `ws://localhost:8000/api/v1/ws`
5. Production fallback: Derived from current location

## Configuration Files

### Frontend Configuration

- `.env.example` - Environment variable template
- `.env.local` - Local development overrides (not committed)
- `src/config/api.ts` - API configuration logic
- `src/lib/api/sixr.ts` - 6R API configuration
- `vite.config.ts` - Vite build configuration

### Backend Configuration

- `backend/env.example` - Backend environment template
- `backend/.env` - Backend environment (not committed)
- `railway.toml` - Railway deployment configuration

## Troubleshooting

### Common Issues

1. **"CORS Error" in production**
   - Ensure `VITE_BACKEND_URL` points to the correct Railway URL
   - **CRITICAL**: Set `ALLOWED_ORIGINS` environment variable in Railway dashboard
   - Include your exact Vercel domain in the ALLOWED_ORIGINS list
   - Restart Railway service after changing environment variables

2. **"Failed to fetch" errors**
   - Check Railway logs for CORS-related errors
   - Verify backend service is running and accessible
   - Test backend health endpoint directly: `https://migrate-ui-orchestrator-production.up.railway.app/health`

3. **"Network Error" in development**
   - Check if Docker containers are running: `docker-compose ps`
   - Verify backend is accessible: `curl http://localhost:8000/health`

4. **Environment variables not working**
   - Ensure variables are prefixed with `VITE_` for frontend
   - Restart development server after changing environment variables
   - Check browser developer tools for actual values

### Debug Commands

```bash
# Check if backend is running
curl http://localhost:8000/health

# Check environment variable resolution
# (Add console.log in src/config/api.ts to see resolved URLs)

# Verify Docker services
docker-compose ps
docker-compose logs backend
docker-compose logs frontend
```

## Best Practices

1. **Never commit `.env` files** containing sensitive data
2. **Use descriptive variable names** with `VITE_` prefix for frontend
3. **Set production variables in deployment platform** (Vercel dashboard)
4. **Test configuration changes** in development before deploying
5. **Document any new environment variables** in this guide

## Production Deployment Checklist

### Before Deploying to Vercel

- [ ] Set `VITE_BACKEND_URL` in Vercel environment variables
- [ ] Optional: Set `VITE_WS_BASE_URL` for WebSocket support
- [ ] Verify Railway backend is running and accessible
- [ ] Test API calls work with Railway URL

### After Deployment

- [ ] Test frontend loads correctly
- [ ] Verify API calls reach Railway backend
- [ ] Check browser developer console for errors
- [ ] Test WebSocket connections (if used)

## Examples

### Example URLs

```bash
# Development
VITE_BACKEND_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000/api/v1/ws

# Production (replace with your actual Railway URL)
VITE_BACKEND_URL=https://migrate-ui-orchestrator-production.up.railway.app
VITE_WS_BASE_URL=wss://migrate-ui-orchestrator-production.up.railway.app/api/v1/ws
```

### Testing Configuration

```javascript
// Add this to src/config/api.ts temporarily for debugging
console.log('API Configuration:', {
  BASE_URL: API_CONFIG.BASE_URL,
  ENV_BACKEND_URL: import.meta.env.VITE_BACKEND_URL,
  ENV_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  DEV_MODE: import.meta.env.DEV,
  MODE: import.meta.env.MODE
});
``` 