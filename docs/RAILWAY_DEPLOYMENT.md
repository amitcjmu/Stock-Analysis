# Railway Deployment Instructions

## 🚨 **Critical Database Setup for Feedback System**

The feedback submission errors in Vercel are caused by database connectivity issues in Railway. Follow these steps to resolve them:

## 📋 **Required Railway Services**

### 1. **PostgreSQL Database Service**
```bash
# Add PostgreSQL service in Railway dashboard:
1. Go to your Railway project
2. Click "New Service" 
3. Select "Database" -> "PostgreSQL"
4. Deploy the database service
```

### 2. **Backend Service Configuration**
```bash
# Required Environment Variables in Railway:
DATABASE_URL          # Automatically set by PostgreSQL service
ENVIRONMENT=production
DEBUG=false
PORT=8000
DEEPINFRA_API_KEY=your_key_here
ALLOWED_ORIGINS=https://aiforce-assess.vercel.app,http://localhost:3000
```

## 🔧 **Database Setup Steps**

### **Step 1: Run Database Migration**
After deploying to Railway, run this command in the Railway console:
```bash
python backend/railway_setup.py
```

### **Step 2: Verify Database Connection**
Check the deployment logs for these success messages:
```
✅ Database Connection: SUCCESS
✅ Database tables created successfully
✅ Feedback System: Operational
```

### **Step 3: Test Feedback Endpoint**
Test the feedback system with curl:
```bash
curl -X POST https://your-railway-app.railway.app/api/v1/discovery/feedback \
  -H "Content-Type: application/json" \
  -d '{"page": "Test", "rating": 5, "comment": "Test", "category": "test", "breadcrumb": "Test", "timestamp": "2025-05-31T06:00:00Z"}'
```

## 🚀 **Automatic Solutions Implemented**

### **1. Graceful Fallback System**
- Main feedback endpoint automatically falls back to in-memory storage if database fails
- Fallback endpoints available at `/api/v1/discovery/feedback/fallback`
- No complete system failure - feedback collection continues

### **2. Enhanced Database Connection**
- Improved PostgreSQL connection handling for Railway
- SSL configuration for Railway PostgreSQL
- Better error handling and logging

### **3. Railway-Specific Configuration**
- `railway.json` deployment configuration
- Automatic database setup script
- Production-ready environment variables

## 🔍 **Troubleshooting**

### **Issue: "Connection refused" errors**
**Solution**: Ensure PostgreSQL service is running and connected to backend service

### **Issue: "Table does not exist" errors**  
**Solution**: Run the migration script: `python backend/railway_setup.py`

### **Issue: Environment variables not set**
**Solution**: Check Railway dashboard environment variables section

### **Issue: CORS errors from Vercel**
**Solution**: Add your Vercel domain to `ALLOWED_ORIGINS` environment variable

## 📊 **Expected Results After Fix**

1. ✅ Feedback submission working from Vercel
2. ✅ No more 500 Internal Server Errors
3. ✅ Database tables created and operational
4. ✅ Graceful fallback if database issues occur
5. ✅ Complete feedback system functionality

## 🔄 **Quick Railway Deployment Commands**

```bash
# 1. Deploy latest code
git push origin main

# 2. Monitor deployment logs
# Check Railway dashboard for deployment status

# 3. Run database setup (in Railway console)
python backend/railway_setup.py

# 4. Test feedback system
curl -X POST https://your-app.railway.app/api/v1/discovery/feedback \
  -H "Content-Type: application/json" \
  -d '{"page": "Railway Test", "rating": 5, "comment": "Testing", "category": "test", "breadcrumb": "Test", "timestamp": "2025-05-31T06:00:00Z"}'
```

## 🎯 **Success Verification**

After following these steps, verify:
- [ ] Railway logs show successful database connection
- [ ] Feedback tables exist in PostgreSQL
- [ ] Feedback submission works from Vercel
- [ ] No 500 errors in Railway logs
- [ ] Fallback system available if needed 