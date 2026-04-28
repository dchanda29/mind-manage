# MindManage — Free Deployment Guide

This guide walks you through deploying **MindManage** for **$0/month** using:

- 🟢 **MongoDB Atlas** (free M0 — 512 MB)
- 🟢 **Render** (free tier for the Python backend)
- 🟢 **Vercel** (free tier for the React frontend)
- 🟢 **Google Gemini 2.5 Flash** (free tier from Google AI Studio)
- 🟢 **Standard Google OAuth 2.0** (free)
- 🟡 **Stripe** (free account — you only pay 2.9% + $0.30 per transaction)

⚠️ **Render free-tier caveat:** The backend will spin down after 15 minutes of inactivity. The first request after that takes ~30–60 seconds. Fine for testing & low traffic, painful at scale.

---

## 0. Prerequisites — accounts you need

| Service | Sign-up link | What you'll grab |
|---|---|---|
| GitHub | https://github.com | Push code (you already have `dchanda29`) |
| MongoDB Atlas | https://www.mongodb.com/cloud/atlas/register | `MONGO_URL` connection string |
| Google Cloud | https://console.cloud.google.com | OAuth Client ID + Client Secret |
| Google AI Studio | https://aistudio.google.com/apikey | `GEMINI_API_KEY` |
| Stripe | https://dashboard.stripe.com/register | `STRIPE_API_KEY` (test mode for now) |
| Render | https://render.com | Backend hosting |
| Vercel | https://vercel.com | Frontend hosting |

---

## 1. Push to GitHub (you do this from chat)

Click the **"Save to GitHub"** button in the Emergent chat input. Push the entire `/app` folder to `dchanda29/mind-manage`.

We're keeping FE and BE in **one monorepo** (simpler — both Render and Vercel can deploy from sub-directories of the same repo).

---

## 2. MongoDB Atlas (~5 min)

1. Sign up at https://www.mongodb.com/cloud/atlas/register
2. **Build a Database** → choose **M0 Free** (any cloud / region near you)
3. **Database Access** → Add a database user (username + password — save these!)
4. **Network Access** → Add IP `0.0.0.0/0` (allow from anywhere, since Render's IP is dynamic)
5. **Database** → **Connect** → **Drivers** → copy the connection string. Looks like:
   ```
   mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
   Replace `<user>` and `<password>` with what you set in step 3.
6. Save this as **`MONGO_URL`**. Use **`DB_NAME=mindmanage_prod`**.

---

## 3. Google Cloud — OAuth 2.0 Client (~10 min)

1. Go to https://console.cloud.google.com → **Select a project** → **New Project** → name it `mindmanage`.
2. Top search bar → **OAuth consent screen** → choose **External** → fill:
   - App name: `MindManage`
   - User support email: `d29chanda@gmail.com`
   - Developer contact: `d29chanda@gmail.com`
   - Save and continue. Skip scopes. Add yourself as a Test user. Save.
3. Top search bar → **Credentials** → **+ Create credentials** → **OAuth client ID**.
   - Application type: **Web application**
   - Name: `MindManage Backend`
   - **Authorized redirect URIs** → add (you'll fill the real Render URL after Step 5):
     ```
     https://mindmanage-backend.onrender.com/api/auth/google/callback
     ```
     (For now you can put a placeholder; come back and edit this after step 5.)
   - Click **Create**.
4. Copy **Client ID** (`xxxx.apps.googleusercontent.com`) and **Client Secret** (`GOCSPX-xxxxx`).
5. Save as `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.

---

## 4. Google AI Studio — Gemini API key (~2 min)

1. Go to https://aistudio.google.com/apikey
2. Click **Create API key** → choose your `mindmanage` project (or create new).
3. Copy the key (starts with `AIza...`).
4. Save as `GEMINI_API_KEY`.

---

## 5. Render — Deploy backend (~10 min)

1. Sign up / sign in at https://render.com (use your GitHub).
2. **New +** → **Web Service** → connect your `dchanda29/mind-manage` repo.
3. Configure:
   - **Name**: `mindmanage-backend`
   - **Region**: closest to you
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**:
     ```
     gunicorn server:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 1 --timeout 120
     ```
   - **Plan**: **Free**
4. **Environment Variables** (click "Advanced"):
   | Key | Value |
   |---|---|
   | `MONGO_URL` | (from step 2) |
   | `DB_NAME` | `mindmanage_prod` |
   | `CORS_ORIGINS` | `https://mindmanage.vercel.app` (you'll update after step 6) |
   | `GOOGLE_CLIENT_ID` | (from step 3) |
   | `GOOGLE_CLIENT_SECRET` | (from step 3) |
   | `GEMINI_API_KEY` | (from step 4) |
   | `STRIPE_API_KEY` | `sk_test_...` (from your Stripe dashboard, test mode) |
   | `BACKEND_PUBLIC_URL` | leave blank for now, fill after first deploy |
   | `FRONTEND_PUBLIC_URL` | leave blank for now, fill after step 6 |
   | `STRIPE_WEBHOOK_SECRET` | leave blank for now (optional, we'll wire later) |
5. Click **Create Web Service**. Render starts building. Wait ~5 min.
6. Once deployed, copy the URL (e.g. `https://mindmanage-backend.onrender.com`).
7. **Update env vars**:
   - Set `BACKEND_PUBLIC_URL=https://mindmanage-backend.onrender.com`
   - Save → Render auto-redeploys.
8. **Update Google OAuth Authorized redirect URI** in Step 3.3 to match the real Render URL.

✅ Test: open `https://mindmanage-backend.onrender.com/api/health` — you should see JSON with `"gemini": true, "stripe": true, "google_oauth": true`.

---

## 6. Vercel — Deploy frontend (~5 min)

1. Sign up / sign in at https://vercel.com (use GitHub).
2. **Add New** → **Project** → import `dchanda29/mind-manage`.
3. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: `Create React App` (auto-detected)
   - **Build Command**: `yarn build` (default)
   - **Output Directory**: `build` (default)
4. **Environment Variables**:
   | Key | Value |
   |---|---|
   | `REACT_APP_BACKEND_URL` | `https://mindmanage-backend.onrender.com` |
5. Click **Deploy**. Wait ~2 min.
6. Copy the deployed URL (e.g. `https://mindmanage.vercel.app`).
7. **Go back to Render** → update env vars:
   - `FRONTEND_PUBLIC_URL=https://mindmanage.vercel.app`
   - `CORS_ORIGINS=https://mindmanage.vercel.app`
   - Save → redeploy.

---

## 7. Stripe (~5 min)

1. Sign up at https://dashboard.stripe.com/register.
2. **Skip** the activation form for now (you can use test mode without activating).
3. **Developers** → **API keys** → copy your **Secret key** (`sk_test_...`).
4. Add to Render env vars as `STRIPE_API_KEY`. Save.
5. **(Optional but recommended)** Set up a webhook:
   - **Developers** → **Webhooks** → **Add endpoint**
   - URL: `https://mindmanage-backend.onrender.com/api/webhook/stripe`
   - Events: `checkout.session.completed`, `checkout.session.async_payment_succeeded`
   - Copy the **Signing secret** (`whsec_...`) → save as `STRIPE_WEBHOOK_SECRET` in Render.
6. **Activate Customer Portal**:
   - **Settings** → **Billing** → **Customer portal** → **Activate**.
7. To go **live**: complete Stripe activation, switch to Live mode, copy `sk_live_...`, replace `STRIPE_API_KEY` in Render. Repeat the webhook setup in Live mode.

---

## 8. Final smoke test

1. Open `https://mindmanage.vercel.app`
2. Click **Continue with Google** → sign in.
3. Land on `/home` with greeting + quote + sub status.
4. Click **Center your mind** → send a message → AI replies (Gemini 2.5 Flash).
5. Send `"i feel like i wanna kill myself"` → see crisis banner with helplines (no LLM call).
6. Click pricing → choose **Monthly** → Stripe checkout → use test card `4242 4242 4242 4242`, any future expiry, any CVC, any ZIP.
7. Land on `/billing/success` → status flips to **Active · Monthly**.
8. Click **Manage / cancel subscription** → opens Stripe Billing Portal.

🎉 You're live.

---

## Day-2 things

- **Cold starts**: Render free tier sleeps. Set up a free uptime monitor (https://uptimerobot.com — ping `/api/health` every 5 minutes) to keep it warm.
- **Custom domain**: Both Vercel and Render support free custom domains. Buy a domain (~$10/yr) and connect.
- **Logs**: Render → your service → **Logs**. Vercel → your project → **Deployments** → **Logs**.
- **Costs to watch**: Atlas M0 (free unless you blow past 512 MB), Gemini free tier (60 RPM, 1500 RPD — plenty for early users), Render free (750 hrs/mo). Stripe takes 2.9% + $0.30/txn.

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `OAuth not configured` on /api/auth/google/start | `GOOGLE_CLIENT_ID` or `BACKEND_PUBLIC_URL` missing in Render env |
| Google `redirect_uri_mismatch` | The URI in Google Cloud Console doesn't EXACTLY match `BACKEND_PUBLIC_URL/api/auth/google/callback` — including trailing slash, http vs https |
| CORS error on FE | `CORS_ORIGINS` in Render doesn't include your Vercel domain |
| 401 on `/api/auth/me` after login | LocalStorage token cleared / cross-origin issue. Check that `REACT_APP_BACKEND_URL` is set in Vercel |
| Stripe checkout 500 | `STRIPE_API_KEY` not set or invalid |
| AI doesn't reply (503) | `GEMINI_API_KEY` invalid or quota exceeded |

---

Need help with any step? Email `d29chanda@gmail.com`.
