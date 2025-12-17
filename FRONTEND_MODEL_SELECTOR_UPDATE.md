# Frontend Model Selector - Update Instructions

## ✅ Changes Made

The model selector component has been added to the Stock Analysis search screen. It appears in two locations:

1. **Initial Search Screen** - Above the search input box
2. **Stock Details View** - In the search bar and in the analysis section

## 🔍 Where to Find It

### Location 1: Initial Search Screen
When you first open the Stock Analysis page (before selecting a stock), you'll see:
- A "Search Stocks" card
- **AI Model selector** with label "AI Model:" above the search input
- Search input box
- Search button

### Location 2: After Selecting a Stock
Once you select a stock:
- **In the top search bar** - Model selector appears next to the search input
- **In the Overview tab** - Model selector appears next to the "Generate AI Analysis" button

## 🚀 To See the Updates

### Option 1: Refresh Your Browser (If using hot reload)
1. Hard refresh your browser: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
2. Or clear cache and reload

### Option 2: Restart Frontend Container
If the changes don't appear after refresh:

```bash
# Restart the frontend container
docker restart migration_frontend

# Or rebuild if needed
docker-compose -f config/docker/docker-compose.dev.yml build frontend
docker-compose -f config/docker/docker-compose.dev.yml up -d frontend
```

### Option 3: Check Browser Console
Open browser DevTools (F12) and check for any errors:
- Look for import errors related to `ModelSelector`
- Check if the component is loading correctly

## 📋 What You Should See

The model selector dropdown should show:
- **Auto (Recommended)** - Automatically select the best model
- **Google Gemini** - Google Gemini 1.5 Pro - Advanced reasoning
- **Llama 4 Maverick** - Meta Llama 4 - Complex analysis
- **Gemma 3 4B** - Google Gemma 3 - Fast & efficient

## 🔧 Troubleshooting

### If the component doesn't appear:

1. **Check if files are in the container:**
   ```bash
   docker exec migration_frontend ls -la /app/src/components/stock/
   docker exec migration_frontend ls -la /app/src/pages/discovery/EnhancedDiscoveryDashboard/
   ```

2. **Check for TypeScript/build errors:**
   ```bash
   docker logs migration_frontend | grep -i error
   ```

3. **Verify the import path:**
   - ModelSelector should import from `'../../ui/select'`
   - EnhancedDiscoveryDashboard should import from `'../../../components/stock/ModelSelector'`

4. **Check browser console for errors:**
   - Open DevTools (F12)
   - Look for any red error messages
   - Check the Network tab for failed module loads

### If you see import errors:

The ModelSelector component path was fixed from `'../ui/select'` to `'../../ui/select'`. If you still see errors, verify:
- The file exists at: `src/components/stock/ModelSelector.tsx`
- The UI component exists at: `src/components/ui/select.tsx`

## ✅ Verification Checklist

- [ ] Model selector appears in the initial search screen
- [ ] Model selector appears after selecting a stock
- [ ] Dropdown shows all 4 model options
- [ ] Selecting a model updates the state
- [ ] Analysis uses the selected model when generating

## 📝 Next Steps

Once you can see the model selector:
1. Select "Google Gemini" from the dropdown
2. Search for a stock
3. Click "Generate AI Analysis"
4. The analysis should use Google Gemini model

Make sure you've set the `GOOGLE_GEMINI_API_KEY` environment variable in your backend!

