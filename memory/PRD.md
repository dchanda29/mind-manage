# MindManage — Product Requirements Doc

## Original Problem Statement (verbatim)
Mental wellbeing & AI therapy bot. Free 1-day trial then weekly/monthly/annual paid. Two services: (a) manage and control your mind, (b) ask for therapy/help (renamed: "Talk it out" / "Support"). AI must redirect to professionals on drastic/fatal mental health signals. Welcome message with mind-wellbeing quote on app open. Save up to 5 chats in memory; oldest auto-deleted. No hardcoded values in BE. Brutal review across Go/Kotlin/Java. Calming dusty-lavender / mauve / wine palette. React FE.

## User Choices (Session 1)
- Backend language: User picked **Go** for "brutal review" exercise. Platform constraint forced **Python/FastAPI** as the actually-runnable choice (supervisor is read-only on uvicorn:8001). User accepted.
- AI: **Claude Sonnet 4.5** via free **EMERGENT_LLM_KEY**.
- Payments: **Stripe** (sk_test_emergent on platform).
- Auth: **Emergent-managed Google OAuth**.
- Palette: **Dusty lavender** (FE pending).

## Architecture
- **Backend**: FastAPI + Motor (async Mongo) + emergentintegrations.
- **DB**: MongoDB collections: `users`, `user_sessions`, `chats` (embedded `messages`), `payment_transactions`.
- **Auth flow**: Emergent /session-data → store httpOnly cookie + DB session (7d).
- **Subscription model**: Per-user `trial_end` (1 day from signup) + `subscription_end`. Access if either > now. Idempotent crediting via `credited` flag on transaction (both polling and webhook paths).
- **Chat memory**: Max 5 chats/user — oldest deleted on creation.
- **Crisis safety**: Keyword detection short-circuits LLM and returns helplines (988, iCall, Samaritans, findahelpline) BEFORE LLM is called. LLM system prompts also enforce safety as defense-in-depth.

## Implemented (✅ tested 100%)
**Date: 2026-04-28**
- ✅ Health, welcome quote rotator (10 curated quotes)
- ✅ Emergent Google OAuth — session exchange, /auth/me, logout
- ✅ Chat CRUD: list, create, get full, delete (+ max-5 enforcement)
- ✅ /chats/message — Claude Sonnet 4.5 chat with mode-specific system prompts ("manage" + "support")
- ✅ Crisis keyword detection bypasses LLM, returns 4 international helplines
- ✅ Subscription packages (weekly $4.99 / monthly $14.99 / annual $99.99)
- ✅ Stripe checkout creation, payment status polling, webhook handler — all idempotent
- ✅ Subscription gating (402 on expired trial)
- ✅ MongoDB indexes for fast lookups, no `_id` leakage anywhere

## Backlog (P0)
- [ ] **Frontend (React, dusty-lavender palette)** — login screen, welcome+quote, mode picker, chat UI, subscription page, billing success/cancel, AuthCallback, ProtectedRoute.
- [ ] Stripe billing portal link (manage/cancel sub).

## Backlog (P1)
- [ ] Mood tracker / daily check-in
- [ ] Voice journaling (Whisper STT)
- [ ] Export chat as PDF (premium)
- [ ] Localized crisis lines based on user IP

## Backlog (P2)
- [ ] Refactor server.py into routers/ (~720 lines now)
- [ ] Multilingual crisis keyword detection
- [ ] Push notifications for daily check-in

## Test Credentials
See `/app/memory/test_credentials.md` and `/app/auth_testing.md`.
