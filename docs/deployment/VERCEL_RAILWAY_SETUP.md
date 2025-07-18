# Vercel Frontend + Railway Backend Deployment Setup

## Overview
This guide covers the configuration needed to deploy the AI Modernize Migration Platform with:
- Frontend on Vercel (`https://aiforce-assess.vercel.app`)
- Backend on Railway (`https://migrate-ui-orchestrator-production.up.railway.app`)

## Frontend Configuration (Vercel)

### Environment Variables
Set these environment variables in your Vercel project settings:

```bash
# Backend API URL - CRITICAL for frontend to connect to backend
VITE_BACKEND_URL=https://migrate-ui-orchestrator-production.up.railway.app

# Optional: Enable debug logging
VITE_DEBUG=true
```

### Vercel Configuration File
Create or update `vercel.json` in the root directory:

```json
{
  "env": {
    "VITE_BACKEND_URL": "https://migrate-ui-orchestrator-production.up.railway.app"
  },
  "build": {
    "env": {
      "VITE_BACKEND_URL": "https://migrate-ui-orchestrator-production.up.railway.app"
    }
  }
}
```

## Backend Configuration (Railway)

### Environment Variables
Set these environment variables in your Railway project:

```bash
# Frontend URL for CORS
FRONTEND_URL=https://aiforce-assess.vercel.app

# Allowed CORS origins (comma-separated)
ALLOWED_ORIGINS=https://aiforce-assess.vercel.app,https://migrate-ui-orchestrator-production.up.railway.app

# Other required variables
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-secure-32-character-secret-key
DEEPINFRA_API_KEY=your-deepinfra-api-key

# Database (usually auto-configured by Railway)
DATABASE_URL=postgresql://...
```

### Backend Code Updates

1. **Update CORS Configuration in `backend/main.py`**:
   - The code already includes the Vercel domain in production CORS origins
   - Ensure the Railway environment is detected properly

2. **Verify Health Check Endpoints**:
   - `/health` - Basic health check
   - `/api/v1/health` - API health check

## Troubleshooting

### CORS Errors
If you see CORS errors in the browser console:

1. **Check Backend Logs**: Verify CORS origins are being loaded correctly
2. **Verify Environment**: Ensure `ENVIRONMENT=production` on Railway
3. **Check Headers**: The backend should return proper CORS headers on OPTIONS requests

### API Connection Issues
If the frontend can't connect to the backend:

1. **Verify Environment Variable**: Check `VITE_BACKEND_URL` is set in Vercel
2. **Check Network Tab**: Ensure requests are going to Railway URL, not Vercel URL
3. **Test Direct Access**: Try accessing `https://migrate-ui-orchestrator-production.up.railway.app/health`

### Common Issues and Solutions

1. **"Failed to fetch" errors**:
   - Usually indicates CORS is blocking the request
   - Check that the backend is running and accessible
   - Verify CORS origins match exactly (including https://)

2. **404 on `/api/v1/health`**:
   - This means the frontend is trying to call its own URL
   - Ensure `VITE_BACKEND_URL` is properly set in Vercel

3. **Preflight request fails**:
   - The OPTIONS request is being blocked
   - Check that all required headers are in the CORS allow list

## Deployment Checklist

### Frontend (Vercel)
- [ ] Set `VITE_BACKEND_URL` environment variable
- [ ] Deploy and wait for build to complete
- [ ] Test that API calls go to Railway backend

### Backend (Railway)
- [ ] Set `FRONTEND_URL` and `ALLOWED_ORIGINS` environment variables
- [ ] Deploy and wait for service to be ready
- [ ] Check logs for CORS configuration output
- [ ] Test `/health` endpoint directly

### Post-Deployment
- [ ] Test login functionality
- [ ] Verify API calls work without CORS errors
- [ ] Check browser console for any errors
- [ ] Test key features (asset inventory, discovery flow, etc.)

## Security Considerations

1. **CORS Origins**: Only add trusted domains to CORS origins
2. **HTTPS Only**: Both Vercel and Railway provide HTTPS by default
3. **API Keys**: Never expose API keys in frontend code
4. **Authentication**: Ensure JWT tokens are properly validated

## Monitoring

1. **Frontend (Vercel)**:
   - Check Vercel dashboard for build logs
   - Monitor browser console for errors
   - Use Network tab to debug API calls

2. **Backend (Railway)**:
   - Check Railway logs for errors
   - Monitor for CORS-related warnings
   - Track API response times

## Next Steps

1. **Update Domain**: Consider moving from `aiforce-assess.vercel.app` to a domain that matches the new branding (AI Modernize)
2. **Add Monitoring**: Set up error tracking (e.g., Sentry) for both frontend and backend
3. **Configure CDN**: Use Vercel's edge network for static assets
4. **Set Up Backups**: Configure database backups on Railway