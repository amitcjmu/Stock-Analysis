# Google Gemini API Setup Guide

This guide explains how to set up Google Gemini API integration for the Stock Analysis platform.

## Prerequisites

1. A Google Cloud account
2. Access to Google AI Studio or Google Cloud Console
3. A Google Gemini API key

## Step 1: Get Your Google Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey) or [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new API key for Gemini
3. Copy the API key (it will look like: `AIzaSy...`)

## Step 2: Install the Required Package

The `google-generativeai` package is already listed in `requirements.txt`. Install it using:

```bash
# If using a virtual environment (recommended)
pip install google-generativeai==0.8.3

# Or if using system Python
pip3 install google-generativeai==0.8.3

# Or install all requirements
pip install -r requirements.txt
```

## Step 3: Set Environment Variable

### Option A: Local Development (.env file)

Create or update `backend/.env` file:

```env
GOOGLE_GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-1.5-pro
```

### Option B: Docker Development

Add to your `.env` file or docker-compose environment:

```env
GOOGLE_GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-1.5-pro
```

Then update `config/docker/docker-compose.dev.yml` (already configured).

### Option C: Production (Railway/Vercel)

1. Go to your Railway project settings
2. Add a new environment variable:
   - Name: `GOOGLE_GEMINI_API_KEY`
   - Value: Your API key
3. Optionally add:
   - Name: `GEMINI_MODEL`
   - Value: `gemini-1.5-pro` (or your preferred model)

### Option D: System Environment Variables

```bash
# Linux/Mac
export GOOGLE_GEMINI_API_KEY=your-api-key-here
export GEMINI_MODEL=gemini-1.5-pro

# Windows (PowerShell)
$env:GOOGLE_GEMINI_API_KEY="your-api-key-here"
$env:GEMINI_MODEL="gemini-1.5-pro"

# Windows (CMD)
set GOOGLE_GEMINI_API_KEY=your-api-key-here
set GEMINI_MODEL=gemini-1.5-pro
```

## Step 4: Verify Installation

1. Start your backend server
2. Check the logs for: `Initialized Google Gemini client for gemini-1.5-pro`
3. If you see a warning about `GOOGLE_GEMINI_API_KEY not set`, the environment variable is not configured correctly

## Available Gemini Models

- `gemini-1.5-pro` (Recommended - Default)
- `gemini-1.5-flash` (Faster, lower cost)
- `gemini-pro` (Legacy)

## Troubleshooting

### Error: "Google Generative AI SDK not available"
- Solution: Run `pip install google-generativeai==0.8.3`

### Error: "GOOGLE_GEMINI_API_KEY not set"
- Solution: Ensure the environment variable is set correctly (see Step 3)

### Error: "Failed to initialize Google Gemini client"
- Solution: Verify your API key is valid and has proper permissions

### Model Selection Not Working
- Solution: Ensure the backend has restarted after setting the environment variable

## Security Notes

⚠️ **Never commit your API key to version control!**

- Add `.env` to `.gitignore` if not already present
- Use environment variables or secret management services in production
- Rotate your API keys regularly

## Testing

After setup, you can test the integration:

1. Open the Stock Analysis UI
2. Select "Google Gemini" from the model dropdown
3. Search for a stock and click "Generate AI Analysis"
4. The analysis should use Google Gemini model

## Support

For issues with:
- **API Key**: Contact Google Cloud Support
- **Integration**: Check backend logs for detailed error messages
- **Model Selection**: Verify the model name matches available models
