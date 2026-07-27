# GTA Running Deals

Running shoe price tracker for the Toronto/GTA region. Scrapes 12 retailer sites daily, detects price drops, and alerts users via email.

## Stack

| Layer | Service |
|---|---|
| Scraping | Python + Playwright + BeautifulSoup (GitHub Actions, free tier) |
| Database | Supabase PostgreSQL (free tier) |
| Backend API | Vercel Serverless Functions / Node.js (free tier) |
| Auth | Supabase Auth (free tier) |
| Rate limiting | Upstash Redis (free tier) |
| Frontend | React + Tailwind CSS on Vercel (free tier) |
| Email alerts | Resend (free tier, 100 emails/day) |
| Maps | Leaflet.js + OpenStreetMap (free, no API key) |

## Setup

### 1. Supabase

1. Create a project at supabase.com
2. Run `supabase/schema.sql` in the SQL editor — creates all tables, indexes, RLS policies, the `get_deals` RPC, and seeds the 12 retailers
3. Copy your project URL and keys

### 2. Upstash Redis

1. Create a Redis database at upstash.com (free tier)
2. Copy REST URL and token

### 3. Resend

1. Create an account at resend.com (free tier: 100 emails/day)
2. Add and verify your sending domain
3. Copy your API key

### 4. GitHub Actions secrets

Add these secrets to your repo (Settings → Secrets → Actions):

```
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
RESEND_API_KEY
DEVELOPER_ALERT_EMAIL
```

### 5. Vercel deployment

1. Import the repo to Vercel
2. Set these environment variables in the Vercel dashboard:

```
SUPABASE_URL
SUPABASE_ANON_KEY
UPSTASH_REDIS_REST_URL
UPSTASH_REDIS_REST_TOKEN
VITE_SUPABASE_URL         (same as SUPABASE_URL — exposed to browser for auth only)
VITE_SUPABASE_ANON_KEY    (same as anon key — exposed to browser for auth only)
RAKUTEN_MID               (affiliate — optional, fill in when enrolled)
CJ_PID                    (affiliate — optional)
IMPACT_IRCLICKID          (affiliate — optional)
MEC_AFFID                 (affiliate — optional)
```

3. Deploy. Vercel auto-detects Vite + serverless functions.

### 6. Local development

```bash
npm install
cp .env.example .env.local
# Fill in VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env.local
npm run dev
```

For the API functions locally, use `vercel dev` which wires up the serverless functions with the Vercel CLI.

## Scraper

The Python scraper lives in `/scraper`. It runs via GitHub Actions at 6am ET daily.

To run locally:

```bash
cd scraper
pip install -r requirements.txt
playwright install chromium
export SUPABASE_URL=...
export SUPABASE_SERVICE_ROLE_KEY=...
export RESEND_API_KEY=...
export DEVELOPER_ALERT_EMAIL=...
python main.py
```

## Free tier limits

| Service | Limit | Strategy |
|---|---|---|
| GitHub Actions | 2,000 min/month | Sequential scrapers (~1,100 min/month) |
| Supabase | 500 MB / 50k rows | 90-day price history rolling window (daily cleanup) |
| Vercel Functions | 100k invocations/month | Max 50 rows per response |
| Upstash Redis | 10k requests/day | 60 req/min per IP rate limit |
| Resend | 100 emails/day | Batched per user |

## Affiliate links

Affiliate parameters are appended at the API layer in `api/lib/affiliates.js`. The database always stores clean URLs. Update tracking codes in that file without touching application logic. See the file for the retailer-to-network mapping.

**Never affiliate-tag URLs in alert emails** — only in API responses used for frontend clickthroughs.
