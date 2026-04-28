"""
MindManage - Mental Wellbeing & AI Therapy Backend
FastAPI + MongoDB + Emergent LLM (Claude Sonnet 4.5) + Stripe + Emergent Google Auth
"""
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Cookie, Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import random
import uuid
import httpx
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime, timezone, timedelta

from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout,
    CheckoutSessionRequest,
)

# ---------- Setup ----------
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mindmanage")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
EMERGENT_AUTH_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

app = FastAPI(title="MindManage API")
api = APIRouter(prefix="/api")

# ---------- Constants ----------
MAX_SAVED_CHATS = 5
TRIAL_DAYS = 1

SUBSCRIPTION_PACKAGES = {
    "weekly":  {"id": "weekly",  "label": "Weekly",  "amount": 4.99,  "currency": "usd", "days": 7},
    "monthly": {"id": "monthly", "label": "Monthly", "amount": 14.99, "currency": "usd", "days": 30},
    "annual":  {"id": "annual",  "label": "Annual",  "amount": 99.99, "currency": "usd", "days": 365},
}

WELCOME_QUOTES = [
    {"text": "You don't have to control your thoughts. You just have to stop letting them control you.", "author": "Dan Millman"},
    {"text": "Your present circumstances don't determine where you can go; they merely determine where you start.", "author": "Nido Qubein"},
    {"text": "Almost everything will work again if you unplug it for a few minutes — including you.", "author": "Anne Lamott"},
    {"text": "Mental health... is not a destination, but a process. It's about how you drive, not where you're going.", "author": "Noam Shpancer"},
    {"text": "Self-care is how you take your power back.", "author": "Lalah Delia"},
    {"text": "You are allowed to be both a masterpiece and a work in progress, simultaneously.", "author": "Sophia Bush"},
    {"text": "What mental health needs is more sunlight, more candor, more unashamed conversation.", "author": "Glenn Close"},
    {"text": "Healing takes time, and asking for help is a courageous step.", "author": "Mariska Hargitay"},
    {"text": "Out of suffering have emerged the strongest souls.", "author": "Khalil Gibran"},
    {"text": "You, yourself, as much as anybody in the entire universe, deserve your love and affection.", "author": "Buddha"},
]

# Crisis keyword detection (defense-in-depth alongside LLM-based detection)
CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "want to die", "killing myself",
    "self harm", "self-harm", "cut myself", "cutting myself",
    "no reason to live", "better off dead", "end it all",
    "overdose", "od myself",
]

CRISIS_RESPONSE = (
    "I hear that you're going through something incredibly painful, and I'm really glad you reached out. "
    "What you're feeling matters, and you deserve support from someone trained to help you through this — "
    "more than I can offer as an AI.\n\n"
    "**Please reach out right now to someone who can be there with you:**\n\n"
    "• **988 Suicide & Crisis Lifeline** (US) — Call or text **988**\n"
    "• **Crisis Text Line** — Text **HOME** to **741741**\n"
    "• **iCall (India)** — **+91 9152987821**\n"
    "• **Samaritans (UK & Ireland)** — **116 123**\n"
    "• **International**: https://findahelpline.com\n\n"
    "If you are in immediate danger, please call your local emergency number or go to the nearest emergency room. "
    "You are not alone in this. I'll be here whenever you want to keep talking."
)

SYSTEM_PROMPTS = {
    "manage": (
        "You are a calm, grounded mental wellbeing coach inside the MindManage app. "
        "Your purpose is to help the user MANAGE AND CONTROL THEIR MIND — focus, mental clarity, "
        "intrusive thoughts, racing thoughts, overthinking, emotional regulation, focus, habits, mindfulness, "
        "and cognitive reframing.\n\n"
        "Style: warm, concise, practical. Offer evidence-informed micro-techniques (CBT reframes, box breathing, "
        "grounding 5-4-3-2-1, urge surfing, thought labeling). Ask one focused question at a time. "
        "Avoid jargon. Use plain, kind language.\n\n"
        "SAFETY: You are NOT a licensed therapist or doctor. If the user mentions self-harm, suicidal thoughts, "
        "abuse, severe trauma, hallucinations, or any crisis — STOP coaching and gently guide them to a "
        "qualified professional or crisis hotline. Always include the 988 (US) / iCall (India) / 116 123 (UK) numbers "
        "when safety is at risk. Never minimize or moralize."
    ),
    "support": (
        "You are a deeply empathetic companion inside MindManage providing SUPPORTIVE LISTENING — "
        "a safe space to talk through what someone is feeling. You are not a therapist; you are a "
        "non-judgmental, present-with-them companion.\n\n"
        "Style: validate first, advise rarely. Reflect feelings back. Use short paragraphs. Ask gentle, "
        "open-ended questions. Avoid toxic positivity. Avoid clinical jargon. Match the user's energy.\n\n"
        "SAFETY (non-negotiable): If the user expresses suicidal ideation, intent to self-harm, abuse, "
        "or any acute crisis — STOP and direct them to professional help (988 US, iCall India +91 9152987821, "
        "Samaritans UK 116 123, or local emergency services). Do not attempt to handle a crisis alone. "
        "You may continue offering presence, but always lead with the resources."
    ),
}

# ---------- Models ----------
class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime
    trial_end: datetime
    subscription_status: Literal["trial", "active", "expired"] = "trial"
    subscription_plan: Optional[str] = None
    subscription_end: Optional[datetime] = None


class ChatSessionMeta(BaseModel):
    chat_id: str
    user_id: str
    title: str
    mode: Literal["manage", "support"]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ChatSessionFull(ChatSessionMeta):
    messages: List[ChatMessage] = []


class CreateChatRequest(BaseModel):
    mode: Literal["manage", "support"] = "support"
    title: Optional[str] = None


class SendMessageRequest(BaseModel):
    chat_id: str
    text: str


class SendMessageResponse(BaseModel):
    user_message: ChatMessage
    assistant_message: ChatMessage
    crisis_detected: bool = False


class CheckoutRequest(BaseModel):
    package_id: Literal["weekly", "monthly", "annual"]
    origin_url: str


class CheckoutResponse(BaseModel):
    url: str
    session_id: str


class PaymentStatusResponse(BaseModel):
    status: str
    payment_status: str
    amount_total: float
    currency: str
    package_id: Optional[str] = None


# ---------- Helpers ----------
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _parse_dt(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return None


def _user_from_doc(doc: dict) -> User:
    return User(
        user_id=doc["user_id"],
        email=doc["email"],
        name=doc["name"],
        picture=doc.get("picture"),
        created_at=_parse_dt(doc["created_at"]),
        trial_end=_parse_dt(doc["trial_end"]),
        subscription_status=doc.get("subscription_status", "trial"),
        subscription_plan=doc.get("subscription_plan"),
        subscription_end=_parse_dt(doc.get("subscription_end")),
    )


def _has_active_access(user: User) -> bool:
    now = _now()
    if user.subscription_end and user.subscription_end > now:
        return True
    if user.trial_end and user.trial_end > now:
        return True
    return False


def _detect_crisis(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in CRISIS_KEYWORDS)


async def _get_user_by_session(request: Request) -> Optional[User]:
    """Read session_token from cookie or Authorization header, return user or None."""
    token = request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        return None

    sess = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not sess:
        return None

    expires_at = _parse_dt(sess.get("expires_at"))
    if not expires_at or expires_at < _now():
        return None

    user_doc = await db.users.find_one({"user_id": sess["user_id"]}, {"_id": 0})
    if not user_doc:
        return None
    return _user_from_doc(user_doc)


async def require_user(request: Request) -> User:
    user = await _get_user_by_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def require_active_user(request: Request) -> User:
    user = await require_user(request)
    if not _has_active_access(user):
        raise HTTPException(status_code=402, detail="Subscription required. Free trial has ended.")
    return user


async def _enforce_chat_limit(user_id: str):
    """Keep at most MAX_SAVED_CHATS chats per user — delete oldest."""
    chats = await db.chats.find({"user_id": user_id}, {"_id": 0, "chat_id": 1, "updated_at": 1}) \
        .sort("updated_at", -1).to_list(length=100)
    if len(chats) > MAX_SAVED_CHATS:
        to_delete = chats[MAX_SAVED_CHATS:]
        ids = [c["chat_id"] for c in to_delete]
        await db.chats.delete_many({"chat_id": {"$in": ids}})


# ---------- Routes: Health & Quotes ----------
@api.get("/health")
async def health():
    return {"status": "ok", "service": "mindmanage", "time": _to_iso(_now())}


@api.get("/quotes/welcome")
async def welcome_quote():
    return random.choice(WELCOME_QUOTES)


# ---------- Routes: Auth (Emergent Google) ----------
@api.post("/auth/session")
async def auth_session(request: Request, response: Response):
    """
    Exchange Emergent session_id (from URL fragment after Google auth) for our session_token.
    Frontend POSTs { session_id }. Backend calls Emergent /session-data, upserts user, sets cookie.
    """
    body = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    # REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    async with httpx.AsyncClient(timeout=15.0) as cli:
        resp = await cli.get(EMERGENT_AUTH_URL, headers={"X-Session-ID": session_id})
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session_id")

    data = resp.json()
    email = data["email"]
    name = data.get("name") or email.split("@")[0]
    picture = data.get("picture")
    session_token = data["session_token"]

    # Upsert user
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    now = _now()
    if existing:
        user_id = existing["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": name, "picture": picture}},
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        trial_end = now + timedelta(days=TRIAL_DAYS)
        await db.users.insert_one({
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "created_at": _to_iso(now),
            "trial_end": _to_iso(trial_end),
            "subscription_status": "trial",
            "subscription_plan": None,
            "subscription_end": None,
        })

    # Store session (7-day expiry, matching Emergent token TTL)
    expires_at = now + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": _to_iso(expires_at),
        "created_at": _to_iso(now),
    })

    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=7 * 24 * 60 * 60,
        path="/",
        secure=True,
        httponly=True,
        samesite="none",
    )
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return _user_from_doc(user_doc).model_dump(mode="json")


@api.get("/auth/me")
async def auth_me(request: Request):
    user = await require_user(request)
    return user.model_dump(mode="json")


@api.post("/auth/logout")
async def auth_logout(request: Request, response: Response):
    token = request.cookies.get("session_token") or ""
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    response.delete_cookie("session_token", path="/")
    return {"ok": True}


# ---------- Routes: Subscription ----------
@api.get("/subscription/packages")
async def list_packages():
    return list(SUBSCRIPTION_PACKAGES.values())


@api.get("/subscription/status")
async def subscription_status(request: Request):
    user = await require_user(request)
    now = _now()
    if user.subscription_end and user.subscription_end > now:
        state, until = "active", user.subscription_end
    elif user.trial_end and user.trial_end > now:
        state, until = "trial", user.trial_end
    else:
        state, until = "expired", None
    return {
        "state": state,
        "plan": user.subscription_plan,
        "until": _to_iso(until) if until else None,
        "has_access": state in ("active", "trial"),
    }


# ---------- Routes: Chats ----------
@api.get("/chats")
async def list_chats(request: Request):
    user = await require_user(request)
    docs = await db.chats.find(
        {"user_id": user.user_id},
        {"_id": 0, "messages": 0},
    ).sort("updated_at", -1).to_list(length=MAX_SAVED_CHATS)
    for d in docs:
        d["created_at"] = _parse_dt(d["created_at"])
        d["updated_at"] = _parse_dt(d["updated_at"])
    return [ChatSessionMeta(**d).model_dump(mode="json") for d in docs]


@api.post("/chats")
async def create_chat(request: Request, payload: CreateChatRequest):
    user = await require_active_user(request)
    now = _now()
    chat_id = f"chat_{uuid.uuid4().hex[:12]}"
    title = payload.title or ("Mind Management" if payload.mode == "manage" else "Talk it out")
    doc = {
        "chat_id": chat_id,
        "user_id": user.user_id,
        "title": title,
        "mode": payload.mode,
        "created_at": _to_iso(now),
        "updated_at": _to_iso(now),
        "message_count": 0,
        "messages": [],
    }
    await db.chats.insert_one(doc)
    await _enforce_chat_limit(user.user_id)
    doc.pop("_id", None)
    doc.pop("messages", None)
    doc["created_at"] = now
    doc["updated_at"] = now
    return ChatSessionMeta(**doc).model_dump(mode="json")


@api.get("/chats/{chat_id}")
async def get_chat(chat_id: str, request: Request):
    user = await require_user(request)
    doc = await db.chats.find_one({"chat_id": chat_id, "user_id": user.user_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Chat not found")
    doc["created_at"] = _parse_dt(doc["created_at"])
    doc["updated_at"] = _parse_dt(doc["updated_at"])
    msgs = []
    for m in doc.get("messages", []):
        msgs.append(ChatMessage(
            role=m["role"],
            content=m["content"],
            created_at=_parse_dt(m["created_at"]),
        ))
    doc["messages"] = msgs
    return ChatSessionFull(**doc).model_dump(mode="json")


@api.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str, request: Request):
    user = await require_user(request)
    res = await db.chats.delete_one({"chat_id": chat_id, "user_id": user.user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"ok": True}


@api.post("/chats/message", response_model=SendMessageResponse)
async def send_message(request: Request, payload: SendMessageRequest):
    user = await require_active_user(request)

    chat_doc = await db.chats.find_one(
        {"chat_id": payload.chat_id, "user_id": user.user_id},
        {"_id": 0},
    )
    if not chat_doc:
        raise HTTPException(status_code=404, detail="Chat not found")

    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    now = _now()
    user_msg = {"role": "user", "content": payload.text.strip(), "created_at": _to_iso(now)}

    crisis = _detect_crisis(payload.text)
    if crisis:
        assistant_text = CRISIS_RESPONSE
    else:
        try:
            assistant_text = await _llm_reply(
                chat_id=payload.chat_id,
                mode=chat_doc["mode"],
                history=chat_doc.get("messages", []),
                new_user_text=payload.text,
            )
        except Exception as e:
            logger.exception("LLM error: %s", e)
            raise HTTPException(status_code=503, detail="AI service unavailable. Please try again.")

    assistant_msg = {"role": "assistant", "content": assistant_text, "created_at": _to_iso(_now())}

    await db.chats.update_one(
        {"chat_id": payload.chat_id, "user_id": user.user_id},
        {
            "$push": {"messages": {"$each": [user_msg, assistant_msg]}},
            "$inc": {"message_count": 2},
            "$set": {"updated_at": _to_iso(_now())},
        },
    )

    return SendMessageResponse(
        user_message=ChatMessage(role="user", content=user_msg["content"], created_at=_parse_dt(user_msg["created_at"])),
        assistant_message=ChatMessage(role="assistant", content=assistant_msg["content"], created_at=_parse_dt(assistant_msg["created_at"])),
        crisis_detected=crisis,
    )


async def _llm_reply(chat_id: str, mode: str, history: list, new_user_text: str) -> str:
    if not EMERGENT_LLM_KEY:
        raise RuntimeError("EMERGENT_LLM_KEY missing")
    system_prompt = SYSTEM_PROMPTS[mode]
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=chat_id,
        system_message=system_prompt,
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")
    # Replay history to keep context (emergentintegrations LlmChat keeps state per session_id internally,
    # but we re-send to be deterministic across server restarts)
    # For efficiency, only send the new message; library tracks per session_id.
    response = await chat.send_message(UserMessage(text=new_user_text))
    return response if isinstance(response, str) else str(response)


# ---------- Routes: Stripe Payments ----------
@api.post("/payments/checkout", response_model=CheckoutResponse)
async def create_checkout(request: Request, payload: CheckoutRequest):
    user = await require_user(request)
    if payload.package_id not in SUBSCRIPTION_PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid package")
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    pkg = SUBSCRIPTION_PACKAGES[payload.package_id]

    # Build URLs from frontend's origin (NEVER hardcoded)
    origin = payload.origin_url.rstrip("/")
    success_url = f"{origin}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/billing/cancel"

    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)

    metadata = {
        "user_id": user.user_id,
        "email": user.email,
        "package_id": payload.package_id,
        "source": "mindmanage_subscription",
    }

    req = CheckoutSessionRequest(
        amount=float(pkg["amount"]),
        currency=pkg["currency"],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata,
    )
    session = await stripe_checkout.create_checkout_session(req)

    await db.payment_transactions.insert_one({
        "session_id": session.session_id,
        "user_id": user.user_id,
        "email": user.email,
        "package_id": payload.package_id,
        "amount": float(pkg["amount"]),
        "currency": pkg["currency"],
        "metadata": metadata,
        "payment_status": "initiated",
        "status": "open",
        "credited": False,
        "created_at": _to_iso(_now()),
    })

    return CheckoutResponse(url=session.url, session_id=session.session_id)


@api.get("/payments/status/{session_id}", response_model=PaymentStatusResponse)
async def payment_status(session_id: str, request: Request):
    user = await require_user(request)
    txn = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not txn or txn["user_id"] != user.user_id:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    status = await stripe_checkout.get_checkout_status(session_id)

    update = {
        "payment_status": status.payment_status,
        "status": status.status,
        "amount_total": status.amount_total,
        "currency": status.currency,
        "updated_at": _to_iso(_now()),
    }
    await db.payment_transactions.update_one({"session_id": session_id}, {"$set": update})

    # Idempotently credit the subscription
    if status.payment_status == "paid" and not txn.get("credited"):
        pkg = SUBSCRIPTION_PACKAGES.get(txn["package_id"])
        if pkg:
            now = _now()
            current_end = _parse_dt((await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "subscription_end": 1})).get("subscription_end"))
            base = current_end if current_end and current_end > now else now
            new_end = base + timedelta(days=pkg["days"])
            await db.users.update_one(
                {"user_id": user.user_id},
                {"$set": {
                    "subscription_status": "active",
                    "subscription_plan": txn["package_id"],
                    "subscription_end": _to_iso(new_end),
                }},
            )
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"credited": True, "credited_at": _to_iso(now)}},
            )

    return PaymentStatusResponse(
        status=status.status,
        payment_status=status.payment_status,
        amount_total=float(status.amount_total) / 100.0,
        currency=status.currency,
        package_id=txn.get("package_id"),
    )


@api.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    if not STRIPE_API_KEY:
        return JSONResponse({"ok": False, "error": "stripe not configured"}, status_code=500)
    body = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    try:
        evt = await stripe_checkout.handle_webhook(body, sig)
    except Exception as e:
        logger.warning("Webhook handle error: %s", e)
        return JSONResponse({"ok": False}, status_code=400)

    txn = await db.payment_transactions.find_one({"session_id": evt.session_id}, {"_id": 0})
    if not txn:
        return {"ok": True}

    await db.payment_transactions.update_one(
        {"session_id": evt.session_id},
        {"$set": {
            "payment_status": evt.payment_status,
            "last_event": evt.event_type,
            "updated_at": _to_iso(_now()),
        }},
    )

    if evt.payment_status == "paid" and not txn.get("credited"):
        pkg = SUBSCRIPTION_PACKAGES.get(txn["package_id"])
        if pkg:
            now = _now()
            udoc = await db.users.find_one({"user_id": txn["user_id"]}, {"_id": 0, "subscription_end": 1})
            current_end = _parse_dt(udoc.get("subscription_end")) if udoc else None
            base = current_end if current_end and current_end > now else now
            new_end = base + timedelta(days=pkg["days"])
            await db.users.update_one(
                {"user_id": txn["user_id"]},
                {"$set": {
                    "subscription_status": "active",
                    "subscription_plan": txn["package_id"],
                    "subscription_end": _to_iso(new_end),
                }},
            )
            await db.payment_transactions.update_one(
                {"session_id": evt.session_id},
                {"$set": {"credited": True, "credited_at": _to_iso(now)}},
            )

    return {"ok": True}


# ---------- App wiring ----------
app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    # Indexes for fast lookups
    await db.users.create_index("user_id", unique=True)
    await db.users.create_index("email", unique=True)
    await db.user_sessions.create_index("session_token", unique=True)
    await db.user_sessions.create_index("user_id")
    await db.chats.create_index([("user_id", 1), ("updated_at", -1)])
    await db.chats.create_index("chat_id", unique=True)
    await db.payment_transactions.create_index("session_id", unique=True)
    logger.info("MindManage backend ready.")


@app.on_event("shutdown")
async def on_shutdown():
    client.close()
