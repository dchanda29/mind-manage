"""
MindManage - Mental Wellbeing & AI Therapy Backend (Portable / Self-hosted edition)

Stack: FastAPI + MongoDB (Motor) + Google Gemini + standard Google OAuth + Stripe.
No Emergent platform dependencies. Deployable on Render, Fly.io, Railway, Docker, anywhere.
"""
from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import random
import uuid
import secrets
import urllib.parse
import httpx
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime, timezone, timedelta
import hashlib
import hmac
from google import genai
from google.genai import types as genai_types

# ---------- Setup ----------
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mindmanage")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
# Public URL of THIS backend (e.g. https://mindmanage-be.onrender.com). Used for OAuth redirect_uri.
BACKEND_PUBLIC_URL = os.environ.get("BACKEND_PUBLIC_URL", "").rstrip("/")
# Public URL of the frontend (e.g. https://mindmanage.vercel.app). Used for post-auth redirect.
FRONTEND_PUBLIC_URL = os.environ.get("FRONTEND_PUBLIC_URL", "").rstrip("/")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_OAUTH_SCOPES = "openid email profile"

mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]

app = FastAPI(title="MindManage API")
api = APIRouter(prefix="/api")

# Lazy LLM client (initialized on first use so server boots without a key for inspection)
_genai_client = None

def get_genai_client():
    global _genai_client
    if _genai_client is None:
        if not GEMINI_API_KEY:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
        _genai_client = genai.Client(api_key=GEMINI_API_KEY)
    return _genai_client


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
    provider: str
    key_id: str
    order_id: str
    amount: int
    currency: str
    name: str
    description: str
    prefill_email: str


class PaymentStatusResponse(BaseModel):
    status: str
    payment_status: str
    amount_total: float
    currency: str
    package_id: Optional[str] = None
    order_id: Optional[str] = None


# ---------- Helpers ----------
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _parse_dt(value):
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
    """Bearer header is the primary mechanism (cross-origin friendly). Cookie fallback supported."""
    token = None
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
    if not token:
        token = request.cookies.get("session_token")
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
    chats = await db.chats.find({"user_id": user_id}, {"_id": 0, "chat_id": 1, "updated_at": 1}) \
        .sort("updated_at", -1).to_list(length=200)
    if len(chats) > MAX_SAVED_CHATS:
        ids = [c["chat_id"] for c in chats[MAX_SAVED_CHATS:]]
        await db.chats.delete_many({"chat_id": {"$in": ids}})


# ---------- Routes: Health & Quotes ----------
@api.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "mindmanage",
        "time": _to_iso(_now()),
        "config": {
            "gemini": bool(GEMINI_API_KEY),
            "razorpay": bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET),
            "google_oauth": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        },
    }


@api.get("/quotes/welcome")
async def welcome_quote():
    return random.choice(WELCOME_QUOTES)


# ---------- Routes: Standard Google OAuth ----------
@api.get("/auth/google/start")
async def auth_google_start(redirect: Optional[str] = None):
    if not (GOOGLE_CLIENT_ID and BACKEND_PUBLIC_URL):
        raise HTTPException(status_code=500, detail="OAuth not configured")
    state = secrets.token_urlsafe(32)
    final_redirect = redirect or (FRONTEND_PUBLIC_URL + "/auth/callback")
    await db.oauth_states.insert_one({
        "state": state,
        "redirect": final_redirect,
        "created_at": _to_iso(_now()),
    })
    params = {
        "response_type": "code",
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": f"{BACKEND_PUBLIC_URL}/api/auth/google/callback",
        "scope": GOOGLE_OAUTH_SCOPES,
        "state": state,
        "prompt": "select_account",
        "access_type": "online",
        "include_granted_scopes": "true",
    }
    return {"url": f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"}


@api.get("/auth/google/callback")
async def auth_google_callback(code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    if error:
        return RedirectResponse(f"{FRONTEND_PUBLIC_URL}/?auth_error={urllib.parse.quote(error)}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code/state")

    state_doc = await db.oauth_states.find_one_and_delete({"state": state})
    if not state_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    # Exchange code for tokens
    async with httpx.AsyncClient(timeout=15.0) as cli:
        token_resp = await cli.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": f"{BACKEND_PUBLIC_URL}/api/auth/google/callback",
            "grant_type": "authorization_code",
        })
        if token_resp.status_code != 200:
            logger.warning("Google token exchange failed: %s", token_resp.text)
            return RedirectResponse(f"{FRONTEND_PUBLIC_URL}/?auth_error=token_exchange_failed")
        access_token = token_resp.json().get("access_token")

        userinfo_resp = await cli.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        if userinfo_resp.status_code != 200:
            return RedirectResponse(f"{FRONTEND_PUBLIC_URL}/?auth_error=userinfo_failed")
        info = userinfo_resp.json()

    email = info["email"]
    name = info.get("name") or email.split("@")[0]
    picture = info.get("picture")

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

    # Create our own session token (opaque, random, cross-origin friendly)
    session_token = "mm_" + secrets.token_urlsafe(40)
    expires_at = now + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": _to_iso(expires_at),
        "created_at": _to_iso(now),
    })

    # Hand off to FE via URL fragment (token is not exposed in server logs / Referer)
    redirect_to = state_doc.get("redirect") or (FRONTEND_PUBLIC_URL + "/auth/callback")
    return RedirectResponse(f"{redirect_to}#token={urllib.parse.quote(session_token)}")


@api.get("/auth/me")
async def auth_me(request: Request):
    user = await require_user(request)
    return user.model_dump(mode="json")


@api.post("/auth/logout")
async def auth_logout(request: Request):
    auth = request.headers.get("Authorization", "")
    token = auth[7:].strip() if auth.startswith("Bearer ") else request.cookies.get("session_token", "")
    if token:
        await db.user_sessions.delete_one({"session_token": token})
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


@api.post("/subscription/portal")
async def subscription_portal(request: Request):
    raise HTTPException(
        status_code=501,
        detail="Razorpay customer self-serve portal is not integrated yet. Contact support to manage cancellations."
    )


@api.get("/streak")
async def streak(request: Request):
    user = await require_user(request)
    docs = await db.chats.find(
        {"user_id": user.user_id},
        {"_id": 0, "updated_at": 1, "created_at": 1, "messages": 1},
    ).to_list(length=200)

    days = set()
    for d in docs:
        for ts in [d.get("updated_at"), d.get("created_at")]:
            dt = _parse_dt(ts)
            if dt:
                days.add(dt.date())
        for m in d.get("messages", []) or []:
            dt = _parse_dt(m.get("created_at"))
            if dt:
                days.add(dt.date())

    today = _now().date()
    yesterday = today - timedelta(days=1)
    if today in days:
        cursor = today
    elif yesterday in days:
        cursor = yesterday
    else:
        return {"streak": 0, "active_today": False}

    count = 0
    while cursor in days:
        count += 1
        cursor = cursor - timedelta(days=1)
    return {"streak": count, "active_today": today in days}


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
        msgs.append(ChatMessage(role=m["role"], content=m["content"], created_at=_parse_dt(m["created_at"])))
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
                mode=chat_doc["mode"],
                history=chat_doc.get("messages", []),
                new_user_text=payload.text,
            )
        except HTTPException:
            raise
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


async def _llm_reply(mode: str, history: list, new_user_text: str) -> str:
    """Call Gemini 2.5 Flash with system prompt + multi-turn history."""
    client = get_genai_client()
    system_prompt = SYSTEM_PROMPTS[mode]

    # Convert our DB history to Gemini Content format
    contents = []
    for m in history:
        role = "user" if m["role"] == "user" else "model"
        contents.append(genai_types.Content(role=role, parts=[genai_types.Part.from_text(text=m["content"])]))
    contents.append(genai_types.Content(role="user", parts=[genai_types.Part.from_text(text=new_user_text)]))

    config = genai_types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.7,
        max_output_tokens=1024,
    )

    # google-genai client.aio for async
    resp = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=config,
    )
    text = (resp.text or "").strip()
    return text or "I'm here. Could you say a little more about what's going on?"


# ---------- Routes: Razorpay Payments ----------
@api.post("/payments/checkout", response_model=CheckoutResponse)
async def create_checkout(request: Request, payload: CheckoutRequest):
    user = await require_user(request)
    if payload.package_id not in SUBSCRIPTION_PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid package")
    if not (RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET):
        raise HTTPException(status_code=500, detail="Razorpay not configured")

    pkg = SUBSCRIPTION_PACKAGES[payload.package_id]
    amount_paise = int(round(pkg["amount"] * 100))

    auth = (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
    order_payload = {
        "amount": amount_paise,
        "currency": pkg["currency"].upper(),
        "receipt": f"mm_{user.user_id}_{uuid.uuid4().hex[:10]}",
        "notes": {
            "user_id": user.user_id,
            "email": user.email,
            "package_id": payload.package_id,
            "source": "mindmanage_subscription",
        },
    }
    async with httpx.AsyncClient(timeout=20.0) as cli:
        r = await cli.post("https://api.razorpay.com/v1/orders", auth=auth, json=order_payload)
    if r.status_code not in (200, 201):
        logger.warning("Razorpay order create failed: %s", r.text)
        raise HTTPException(status_code=502, detail="Razorpay order creation failed")
    order = r.json()
    order_id = order.get("id")
    if not order_id:
        raise HTTPException(status_code=502, detail="Razorpay returned invalid order")

    await db.payment_transactions.insert_one({
        "order_id": order_id,
        "user_id": user.user_id,
        "email": user.email,
        "package_id": payload.package_id,
        "amount": float(pkg["amount"]),
        "amount_paise": amount_paise,
        "currency": pkg["currency"].upper(),
        "metadata": order_payload["notes"],
        "payment_status": "initiated",
        "status": order.get("status", "created"),
        "credited": False,
        "created_at": _to_iso(_now()),
    })
    return CheckoutResponse(
        provider="razorpay",
        key_id=RAZORPAY_KEY_ID,
        order_id=order_id,
        amount=amount_paise,
        currency=pkg["currency"].upper(),
        name="MindManage",
        description=f"MindManage {pkg['label']} plan",
        prefill_email=user.email,
    )


async def _credit_subscription(user_id: str, package_id: str):
    pkg = SUBSCRIPTION_PACKAGES.get(package_id)
    if not pkg:
        return
    now = _now()
    udoc = await db.users.find_one({"user_id": user_id}, {"_id": 0, "subscription_end": 1})
    if not udoc:
        return
    current_end = _parse_dt(udoc.get("subscription_end"))
    base = current_end if current_end and current_end > now else now
    new_end = base + timedelta(days=pkg["days"])
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "subscription_status": "active",
            "subscription_plan": package_id,
            "subscription_end": _to_iso(new_end),
        }},
    )


@api.get("/payments/status/{order_id}", response_model=PaymentStatusResponse)
async def payment_status(order_id: str, request: Request):
    user = await require_user(request)
    txn = await db.payment_transactions.find_one({"order_id": order_id}, {"_id": 0})
    if not txn or txn["user_id"] != user.user_id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    payment_status = "paid" if txn.get("credited") else txn.get("payment_status", "created")
    status = "paid" if txn.get("credited") else txn.get("status", "created")

    return PaymentStatusResponse(
        status=status,
        payment_status=payment_status,
        amount_total=float(txn.get("amount", 0.0)),
        currency=(txn.get("currency") or "INR").lower(),
        package_id=txn.get("package_id"),
        order_id=txn.get("order_id"),
    )


@api.post("/payments/verify")
async def verify_payment(request: Request):
    user = await require_user(request)
    body = await request.json()
    razorpay_order_id = body.get("razorpay_order_id")
    razorpay_payment_id = body.get("razorpay_payment_id")
    razorpay_signature = body.get("razorpay_signature")
    if not (razorpay_order_id and razorpay_payment_id and razorpay_signature):
        raise HTTPException(status_code=400, detail="Missing verification fields")
    if not RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=500, detail="Razorpay not configured")

    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode("utf-8"),
        f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid Razorpay signature")

    txn = await db.payment_transactions.find_one({"order_id": razorpay_order_id}, {"_id": 0})
    if not txn or txn["user_id"] != user.user_id:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if not txn.get("credited"):
        await _credit_subscription(user.user_id, txn["package_id"])
    await db.payment_transactions.update_one(
        {"order_id": razorpay_order_id},
        {"$set": {
            "status": "paid",
            "payment_status": "captured",
            "payment_id": razorpay_payment_id,
            "signature": razorpay_signature,
            "credited": True,
            "credited_at": _to_iso(_now()),
            "updated_at": _to_iso(_now()),
        }},
    )
    return {"ok": True, "order_id": razorpay_order_id, "payment_id": razorpay_payment_id}


@api.post("/webhook/razorpay")
async def razorpay_webhook(request: Request):
    if not RAZORPAY_KEY_SECRET:
        return JSONResponse({"ok": False, "error": "razorpay not configured"}, status_code=500)
    body = await request.body()
    sig_header = request.headers.get("x-razorpay-signature", "")
    try:
        if not RAZORPAY_WEBHOOK_SECRET:
            return JSONResponse({"ok": True, "ignored": "webhook secret not configured"})
        expected = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, sig_header):
            return JSONResponse({"ok": False}, status_code=400)
        import json
        event = json.loads(body.decode("utf-8"))
    except Exception as e:
        logger.warning("Webhook verification failed: %s", e)
        return JSONResponse({"ok": False}, status_code=400)

    if event.get("event") == "payment.captured":
        payment = (event.get("payload") or {}).get("payment", {}).get("entity", {})
        order_id = payment.get("order_id")
        payment_id = payment.get("id")
        txn = await db.payment_transactions.find_one({"order_id": order_id}, {"_id": 0})
        if txn and not txn.get("credited"):
            await _credit_subscription(txn["user_id"], txn["package_id"])
            await db.payment_transactions.update_one(
                {"order_id": order_id},
                {"$set": {
                    "credited": True,
                    "credited_at": _to_iso(_now()),
                    "payment_status": "captured",
                    "status": "paid",
                    "payment_id": payment_id,
                    "last_event": event.get("event"),
                    "updated_at": _to_iso(_now()),
                }},
            )

    return {"ok": True}


# ---------- App wiring ----------
app.include_router(api)

_cors_raw = os.environ.get("CORS_ORIGINS", "*")
_cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    await db.users.create_index("user_id", unique=True)
    await db.users.create_index("email", unique=True)
    await db.user_sessions.create_index("session_token", unique=True)
    await db.user_sessions.create_index("user_id")
    await db.chats.create_index([("user_id", 1), ("updated_at", -1)])
    await db.chats.create_index("chat_id", unique=True)
    await db.payment_transactions.create_index("order_id", unique=True)
    await db.oauth_states.create_index("created_at", expireAfterSeconds=600)  # auto-clean stale states
    logger.info("MindManage backend ready (portable mode).")


@app.on_event("shutdown")
async def on_shutdown():
    mongo_client.close()
