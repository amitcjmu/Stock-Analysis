# Upstash Redis Production Setup Guide

## Overview

This guide provides **exactly what you need** to deploy Redis caching with Upstash in production using Railway backend and Vercel frontend. No confusing hundreds of variables - just the essentials.

## Prerequisites

- **Railway.app account** (for backend deployment)
- **Vercel account** (for frontend deployment)
- **Upstash account** (free tier available at [upstash.com](https://upstash.com))

## Step 1: Create Upstash Redis Database

1. Go to [Upstash Console](https://console.upstash.com)
2. Click **"Create Database"**
3. Choose:
   - **Name**: `migrate-ui-orchestrator-prod`
   - **Region**: Choose closest to your Railway region
   - **Type**: Redis (not Kafka)
4. Click **"Create"**
5. **Copy these values** from the database details:
   - `UPSTASH_REDIS_REST_URL` (looks like: `https://xyz-abc123.upstash.io`)
   - `UPSTASH_REDIS_REST_TOKEN` (long string starting with `A...`)

## Step 2: Railway Backend Configuration

### Required Environment Variables

Set these in your Railway project environment variables:

```bash
# MANDATORY: Upstash Redis Configuration
UPSTASH_REDIS_URL=https://your-endpoint.upstash.io
UPSTASH_REDIS_TOKEN=AxxCz...your-long-token-here

# OPTIONAL: Redis Optimization (only change if you hit limits)
UPSTASH_DAILY_LIMIT=10000
REDIS_ENABLED=true
REDIS_DEFAULT_TTL=3600
```

### How to Set Railway Environment Variables

1. Go to your Railway project dashboard
2. Select your backend service
3. Click **Variables** tab
4. Add each variable above
5. Deploy your service

## Step 3: Vercel Frontend Configuration (If Needed)

**Most likely NOT needed** - the frontend doesn't directly connect to Redis. But if you need it:

```bash
# Only add these to Vercel if your frontend needs direct Redis access
UPSTASH_REDIS_URL=https://your-endpoint.upstash.io
UPSTASH_REDIS_TOKEN=AxxCz...your-long-token-here
```

### How to Set Vercel Environment Variables

1. Go to your Vercel project dashboard
2. Click **Settings** → **Environment Variables**
3. Add variables if needed
4. Redeploy your frontend

## Step 4: Verify Setup

### Test Redis Connection

1. Deploy your Railway backend with the new variables
2. Check Railway logs for:
   ```
   INFO: Connected to Upstash Redis (Production)
   ```

### Health Check Endpoint

Hit your backend health endpoint:
```bash
curl https://your-railway-app.com/api/v1/health
```

Should include Redis status:
```json
{
  "redis": {
    "status": "healthy",
    "client_type": "upstash",
    "latency_ms": 45.2
  }
}
```

## Step 5: Security Verification

### Upstash Security Features (Built-in)

✅ **TLS/SSL encryption** - Always enabled
✅ **Authentication** - Token-based auth
✅ **Network isolation** - No public access without token
✅ **Rate limiting** - Built into our configuration

### What's Already Secured

The existing `upstash_config.py` already handles:
- Connection pooling with SSL
- Rate limiting (10,000 commands/day free tier)
- Circuit breaker pattern for failures
- Automatic retry logic
- Command cost estimation

## Troubleshooting

### Issue: "upstash-redis package not installed"

**Solution**: Already included in requirements.txt - redeploy Railway service

### Issue: "Rate limit exceeded"

**Solutions**:
1. **Free tier limit**: 10,000 commands/day
2. **Upgrade Upstash plan** for higher limits
3. **Optimize caching**: Increase TTL values

### Issue: High latency

**Solutions**:
1. **Check Upstash region** - should match Railway region
2. **Review cache strategy** - cache frequently accessed data
3. **Monitor usage** via health endpoint

### Issue: Connection failures

**Check**:
1. **Correct URL format**: Must start with `https://`
2. **Valid token**: Copy from Upstash console exactly
3. **Railway logs**: Check for connection errors

## Cost Optimization

### Free Tier Limits
- **10,000 commands/day**
- **100 MB storage**
- **100 concurrent connections**

### Monitor Usage

Check usage via API:
```bash
curl https://your-railway-app.com/api/v1/health
```

Look for `upstash_metrics` section showing current usage.

### Upgrade Path

When you exceed free tier:
- **Paid tier**: $0.20 per 100K commands
- **Automatic scaling** based on usage
- **No service interruption**

## What You DON'T Need

❌ **Redis passwords** - Upstash uses token auth
❌ **Redis configuration files** - Managed by Upstash
❌ **SSL certificates** - Handled automatically
❌ **Backup configuration** - Built into Upstash
❌ **Cluster setup** - Single instance sufficient
❌ **Redis Sentinel** - Upstash handles failover

## Production Checklist

- [ ] Upstash database created
- [ ] Railway environment variables set
- [ ] Backend deployed and showing Redis connection
- [ ] Health check endpoint returning Redis status
- [ ] Vercel frontend deployed (Redis variables optional)
- [ ] Monitoring setup for usage tracking

## Quick Start Commands

```bash
# Test connection from your backend
curl https://your-railway-app.com/api/v1/health | jq '.redis'

# Check Railway logs for Redis connection
railway logs

# Monitor Upstash usage
# (View in Upstash Console → Database → Metrics)
```

## Summary

**Exactly 2 environment variables** are required for Railway:
1. `UPSTASH_REDIS_URL`
2. `UPSTASH_REDIS_TOKEN`

**Frontend (Vercel)**: Usually needs **0 variables** for Redis.

**Total setup time**: ~10 minutes

Your production Redis caching is now ready!
