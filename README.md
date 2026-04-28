# MindManage

> A quiet place for your mind. AI-assisted wellbeing companion with two modes — *Center your mind* and *A listening ear* — built for empathetic conversation, gentle reflection, and crisis-aware safety.

Built on **React** (frontend) + **FastAPI / Python** (backend) + **MongoDB**, with **Claude Sonnet 4.5** via the Emergent LLM key, **Stripe** subscriptions, and **Emergent-managed Google OAuth**.

---

## ✨ Features

- 🌿 **1-day free trial**, then weekly / monthly / annual subscription via Stripe
- 🧠 Two chat modes: **Center your mind** (mind-management coaching) and **A listening ear** (empathetic listening)
- 🛡️ **Crisis safety**: keyword detection short-circuits the LLM and surfaces 988 / iCall / Samaritans helplines
- 💾 **Last 5 chats** auto-retained per user (oldest deleted)
- 🔥 **Streak counter** for daily check-ins (retention)
- 🔐 Google OAuth (Emergent-managed)
- 💜 Calming dusty-lavender palette, Spectral + Figtree typography, mobile-first
- 📜 Terms of Service + Privacy Policy pages, Stripe Billing Portal integration

---

## 🏗️ Architecture

```
React (CRA)  ──API──▶  FastAPI (uvicorn)  ──▶  MongoDB
/app/frontend         /app/backend             users / chats / sessions / payments
                        │
                        ├─▶ Anthropic Claude 4.5 (via Emergent LLM key)
                        ├─▶ Stripe Checkout + Billing Portal
                        └─▶ Emergent OAuth /session-data
```

---

## 🔑 Environment Variables

### Backend (`/app/backend/.env`) — see `.env.example`
| Key | Purpose |
|---|---|
| `MONGO_URL` | MongoDB connection string |
| `DB_NAME` | Database name |
| `CORS_ORIGINS` | Comma-separated allowed origins (production: avoid `*`) |
| `EMERGENT_LLM_KEY` | Free Claude/GPT/Gemini access via Emergent platform |
| `STRIPE_API_KEY` | `sk_test_emergent` for dev, `sk_live_…` for production |

### Frontend (`/app/frontend/.env`) — see `.env.example`
| Key | Purpose |
|---|---|
| `REACT_APP_BACKEND_URL` | Public backend URL (no trailing slash) |

---

## 🚀 Local Development (on Emergent)

Backend, frontend, and MongoDB are all managed by supervisor.

```bash
# Logs
tail -f /var/log/supervisor/backend.*.log
tail -f /var/log/supervisor/frontend.*.log

# Restart after env changes
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

---

## 🌍 Production Deployment Checklist

### 1. Pre-deploy hygiene
- [ ] Remove all `*` from `CORS_ORIGINS` — set the exact production origin(s)
- [ ] Confirm Stripe is in **live mode** (`sk_live_…`)
- [ ] Update `MONGO_URL` to MongoDB Atlas (or other production cluster)
- [ ] Verify `EMERGENT_LLM_KEY` has sufficient credits
- [ ] Replace placeholder emails (`hello@mindmanage.app`) with your real contact

### 2. MongoDB Atlas (free tier OK for v1)
- Sign up at https://www.mongodb.com/cloud/atlas/register
- Create a free M0 cluster (512MB)
- Add a database user, allow IP `0.0.0.0/0` (or Emergent's egress IP)
- Copy connection string → set as `MONGO_URL`
- Set `DB_NAME=mindmanage_prod`

### 3. Stripe (live mode)
- In Stripe Dashboard → switch to **Live mode**
- Copy your **Live Secret Key** (`sk_live_…`)
- Set as `STRIPE_API_KEY` in production env
- Activate **Stripe Billing Portal**: Settings → Billing → Customer portal → Activate
- (Optional) Set webhook endpoint to `https://yourdomain.com/api/webhook/stripe`

### 4. Google OAuth (Emergent-managed)
- After deploying with a custom domain, email **support@emergent.sh**
- Request whitelisting your production domain for OAuth redirects
- The auth flow on `auth.emergentagent.com` will then accept your domain

### 5. Custom domain
- In the Emergent dashboard → **Link Domain** → enter your domain
- Click **Entri** → follow DNS instructions
- Remove existing A records at your registrar; let Entri set them
- Wait 5–15 minutes for propagation

### 6. Deploy
- Click **Deploy Now** in the Emergent dashboard
- Wait 10–15 minutes
- Visit your URL and run a real signup → trial → subscribe → chat → cancel test

### 7. Legal & compliance
- [ ] Update `/legal/terms` with your real entity name and jurisdiction
- [ ] Update `/legal/privacy` with your data-processing reality
- [ ] Add a working contact email for GDPR/CCPA requests

---

## 💸 Cost (rough, low-traffic v1)

| Item | Monthly |
|---|---|
| Emergent native deployment | 50 credits/month |
| MongoDB Atlas M0 | $0 |
| Stripe | 2.9% + $0.30 / transaction |
| EMERGENT_LLM_KEY | Per-call from Emergent credits |
| Domain | ~$1/month |

You break even at ~1 paying user/month on the monthly plan ($14.99).

---

## 🧪 Testing

Test sessions are seeded directly in MongoDB — see `/app/auth_testing.md`.

---

## 🙏 Crisis disclaimer

MindManage is supportive software, **not a medical service**. If you or someone you know is in crisis:
- **988** (US) — Suicide & Crisis Lifeline
- **iCall +91 9152987821** (India)
- **Samaritans 116 123** (UK & Ireland)
- **https://findahelpline.com** (international)
- **Local emergency number** in life-threatening situations

---

Built with care on [Emergent](https://emergent.sh).
