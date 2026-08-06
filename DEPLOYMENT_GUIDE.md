# Deploying the Coffee Analytics Platform to Railway

This guide provides step-by-step instructions for deploying the Coffee Analytics Platform to Railway, including how to obtain the necessary API keys for Reddit and Twitter/X.

## Prerequisites

Before deploying, ensure you have the following:
1. A GitHub account with the project repository created
2. A Railway account (sign up at [railway.app](https://railway.app))
3. API credentials for Reddit and Twitter/X (instructions below)

---

## Part 1: Obtaining Reddit API Credentials

The Reddit scraper uses the PRAW (Python Reddit API Wrapper) library, which requires a `Client ID` and `Client Secret` [1].

### Step 1: Create a Reddit App

1. Log in to your Reddit account at [reddit.com](https://www.reddit.com)
2. Navigate to the app preferences page: [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
3. Scroll to the bottom and click **"are you a developer? create an app..."**
4. Fill in the form:

| Field | Value |
|-------|-------|
| Name | `coffee-analytics` (or any name you prefer) |
| App type | Select **"script"** |
| Description | `Coffee analytics platform - social media data scraper` |
| About URL | (optional) Leave blank or add your GitHub repo URL |
| Redirect URI | `http://localhost:8000` |

5. Click **"create app"**

### Step 2: Copy Your Credentials

After creating the app, you will see your credentials displayed:

```
personal use script
coffee-analytics
a string of letters and numbers (this is your Client ID)

secret
a longer string of letters and numbers (this is your Client Secret)
```

Save both values — you will need them for Railway environment variables.

---

## Part 2: Obtaining Twitter/X API Credentials

The Twitter/X scraper uses the v2 API, which requires a **Bearer Token** [2].

### Important: X API Pricing Changes

As of 2024, Twitter/X restructured its API access. The **Free tier** only allows posting tweets — it does not allow reading/searching tweets. To use the search functionality, you need at least the **Basic tier** ($100/month) [3].

> **Alternative:** If you do not want to pay for the Twitter/X API, the platform will automatically fall back to generating mock data. The dashboard will still function fully with mock data.

### Step 1: Sign Up for X Developer Account

1. Go to [https://developer.x.com](https://developer.x.com)
2. Sign in with your X (Twitter) account
3. Complete the onboarding process:
   - Select your use case (choose **"Hobbyist"** or **"Exploring the API"**)
   - Fill in required details about your project

### Step 2: Create an App

1. In the Developer Portal, click **"Projects & Apps"**
2. Click **"Create App"**
3. Provide a name: `coffee-analytics`
4. Once created, navigate to **"Keys and Tokens"**

### Step 3: Copy Your Bearer Token

In the **"Keys and Tokens"** section, you will find:
- **Bearer Token** — copy this value
- **API Key** (also called Consumer Key)
- **API Key Secret** (also called Consumer Secret)

For this project, only the **Bearer Token** is required. Save it securely.

---

## Part 3: Preparing Your GitHub Repository

Before deploying to Railway, ensure your project is on GitHub.

### Step 1: Create a GitHub Repository

```bash
cd coffee_analytics
git init
git add .
git commit -m "Initial commit: Coffee Analytics Platform"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/coffee-analytics.git
git push -u origin main
```

### Step 2: Verify Repository Structure

Ensure your repository contains these files at the root:

```
coffee-analytics/
├── README.md
├── main.py
├── config.py
├── models.py
├── database.py
├── requirements.txt
├── .env.example
├── .gitignore
├── railway.json          # Railway deployment config
├── Dockerfile            # Fallback deployment option
├── api/
├── scraper/
├── processor/
├── dashboard/
└── tests/
```

---

## Part 4: Deploying to Railway

### Step 1: Create a New Project

1. Go to [https://railway.app/dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Click **"Deploy from GitHub repo"**
4. Select your `coffee-analytics` repository
5. Click **"Deploy"**

### Step 2: Configure Environment Variables

Railway will start building, but first you need to set up environment variables:

1. In your project, click on the service card
2. Go to the **"Variables"** tab
3. Click **"New Variable"** and add the following:

| Variable | Value | Required? |
|----------|-------|-----------|
| `REDDIT_CLIENT_ID` | Your Reddit Client ID | Optional* |
| `REDDIT_CLIENT_SECRET` | Your Reddit Client Secret | Optional* |
| `REDDIT_USER_AGENT` | `coffee-analytics/1.0 by /u/YOUR_USERNAME` | Optional |
| `TWITTER_BEARER_TOKEN` | Your Twitter/X Bearer Token | Optional* |
| `DASHBOARD_PORT` | `8000` | Required |
| `DEBUG_MODE` | `false` | Required |
| `DATABASE_URL` | `sqlite:///./data/coffee_analytics.db` | Required |

> *Variables marked "Optional" — if you leave them blank, the platform uses mock data instead.

### Step 3: Set the Start Command

1. Go to the **"Settings"** tab of your service
2. Under **"Start Command"**, set:
   ```
   python3 main.py
   ```

### Step 4: Configure the Builder

Railway will automatically detect this as a Python project using Nixpacks. The `railway.json` configuration file handles this automatically. If you need to customize:

1. Go to **"Settings"** → **"Build"**
2. Select **"Nixpacks"** as the builder (this is the default)
3. The builder will automatically:
   - Detect Python from `requirements.txt`
   - Install all dependencies
   - Run the start command

### Step 5: Wait for Deployment

1. Watch the **"Deployments"** tab for the build progress
2. Once complete, you will see a **"Generate Domain"** button
3. Click it to get a public URL for your dashboard
4. The URL will look like: `https://your-project.up.railway.app`

---

## Part 5: Persistent Storage (SQLite)

Railway services are ephemeral by default — if the service restarts, SQLite data is lost. To persist data:

### Option A: Railway Volumes (Recommended)

1. Go to **"Settings"** → **"Volumes"**
2. Click **"New Volume"**
3. Mount path: `/app/data`
4. This ensures the SQLite database survives restarts

### Option B: Upgrade to PostgreSQL (Production)

For production, consider using Railway's PostgreSQL add-on:

1. In your project, click **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Wait for it to provision
3. Copy the `DATABASE_URL` from the PostgreSQL service variables
4. Add it as a variable in your main service (Railway auto-links services)
5. Update `config.py` to use the PostgreSQL URL

---

## Part 6: Verify Deployment

After deployment, verify everything works:

1. **Dashboard:** Open `https://your-project.up.railway.app` in your browser
2. **API Docs:** Open `https://your-project.up.railway.app/docs`
3. **Health Check:** Open `https://your-project.up.railway.app/api/health`

Expected response from `/api/health`:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "database": "connected",
    "scraper": "ready",
    "processor": "ready",
    "analytics": "ready"
  }
}
```

---

## Part 7: Scheduled Scraping

The platform is designed to run scraping on demand via the API endpoint. To set up automated scraping:

### Using Railway Cron (Scheduled Tasks)

1. Install the Railway CLI:
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. Add a cron job that hits the scrape endpoint:
   ```bash
   railway run curl -X POST https://your-project.up.railway.app/api/scrape \
     -H "Content-Type: application/json" \
     -d '{"force": true}'
   ```

3. Schedule this in Railway's UI or use an external cron service (e.g., Cron-Job.org, EasyCron)

---

## Troubleshooting

### Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Build fails with "module not found" | Missing dependency in `requirements.txt` | Add the missing package and push to GitHub |
| `502 Bad Gateway` on dashboard | Port mismatch | Ensure `DASHBOARD_PORT=8000` is set |
| `0 posts` in dashboard | No API credentials | Platform uses mock data; add Reddit/Twitter keys |
| SQLite data lost after restart | No volume mounted | Add a persistent volume at `/app/data` |
| Reddit API returns 403 | Rate limited or invalid credentials | Check `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` |
| Twitter API returns 403 | Free tier doesn't allow search | Upgrade to Basic tier or use mock data |

### Logs

To view deployment logs:
1. Go to your Railway project
2. Click on the service
3. Select **"Deployments"** → click the latest deployment
4. View the **"Logs"** tab

---

## References

[1] Reddit API Documentation — https://www.reddit.com/dev/api/
[2] X (Twitter) API Documentation — https://docs.x.com/x-api/introduction
[3] X API Pricing — https://docs.x.com/x-api/getting-started/pricing

---

*Guide prepared by Manus AI*
