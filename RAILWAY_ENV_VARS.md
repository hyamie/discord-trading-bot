# Railway Environment Variables Setup

## Copy these into Railway Dashboard

Go to your Railway project → Variables tab → Add these one by one:

### Required (Must have these for deployment to work):

```
ANTHROPIC_API_KEY=sk-ant-api03-[your-key-here]
SCHWAB_API_KEY=[your-schwab-app-key]
SCHWAB_API_SECRET=[your-schwab-secret]
SCHWAB_REDIRECT_URI=https://localhost:8080/callback
```

### Optional (Can add later):

```
FINNHUB_API_KEY=[your-finnhub-key]
NEWSAPI_KEY=[your-newsapi-key]
```

### Auto-configured by Railway (Don't add these):

```
PORT - Railway sets this automatically
RAILWAY_ENVIRONMENT - Railway sets this automatically
```

---

## Where to Get API Keys:

### 1. Anthropic Claude API Key
- URL: https://console.anthropic.com
- Steps:
  1. Sign up/login
  2. Click "API Keys" in sidebar
  3. Click "Create Key"
  4. Copy the key (starts with `sk-ant-api03-...`)
  5. Paste into Railway as `ANTHROPIC_API_KEY`

### 2. Schwab API Credentials
- URL: https://developer.schwab.com
- Steps:
  1. Login to your developer account
  2. Go to "Apps" → Select your app
  3. Copy "App Key" → Paste as `SCHWAB_API_KEY`
  4. Copy "Secret" → Paste as `SCHWAB_API_SECRET`
  5. Set `SCHWAB_REDIRECT_URI=https://localhost:8080/callback`

### 3. Finnhub (Optional - for news)
- URL: https://finnhub.io
- Free tier: 60 calls/min
- Sign up → Dashboard → Copy API key

### 4. NewsAPI (Optional - for market news)
- URL: https://newsapi.org
- Free tier: 100 requests/day
- Sign up → Get API Key

---

## After Adding Variables:

Railway will automatically **redeploy** your service. Watch the deployment logs.

Expected result:
- Build should succeed (30-60 seconds)
- Health check should pass
- You'll get a public URL like: `https://discord-trading-bot-production-xxxx.up.railway.app`

Test it:
```bash
curl https://your-railway-url.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-13T...",
  "version": "1.0.0"
}
```
