"""MindManage backend test suite (pytest)."""
import os
import time
import uuid
import subprocess
import requests
import pytest
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://mental-care-pro-2.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


def _seed_user(trial_offset_seconds=86400, subscription_status="trial", subscription_end_offset=None, plan=None):
    """Seed a user + session via mongosh. Returns (token, user_id, email)."""
    token = f"test_session_{uuid.uuid4().hex}"
    user_id = f"test-user-{uuid.uuid4().hex[:12]}"
    email = f"tester+{uuid.uuid4().hex[:8]}@mindmanage.test"
    now_ms = int(time.time() * 1000)
    trial_end_ms = now_ms + int(trial_offset_seconds * 1000)
    sub_end_js = "null"
    if subscription_end_offset is not None:
        sub_end_ms = now_ms + int(subscription_end_offset * 1000)
        sub_end_js = f"new Date({sub_end_ms}).toISOString()"
    plan_js = "null" if plan is None else f"'{plan}'"
    js = f"""
use('test_database');
db.users.insertOne({{
  user_id: '{user_id}',
  email: '{email}',
  name: 'Test User',
  picture: null,
  created_at: new Date({now_ms}).toISOString(),
  trial_end: new Date({trial_end_ms}).toISOString(),
  subscription_status: '{subscription_status}',
  subscription_plan: {plan_js},
  subscription_end: {sub_end_js}
}});
db.user_sessions.insertOne({{
  user_id: '{user_id}',
  session_token: '{token}',
  expires_at: new Date({now_ms + 7*86400*1000}).toISOString(),
  created_at: new Date({now_ms}).toISOString()
}});
"""
    r = subprocess.run(["mongosh", "--quiet", "--eval", js], capture_output=True, text=True, timeout=15)
    assert r.returncode == 0, f"mongosh seed failed: {r.stderr}"
    return token, user_id, email


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def cleanup():
    yield
    subprocess.run(["mongosh", "--quiet", "--eval",
        "use('test_database'); db.users.deleteMany({email:/@mindmanage\\.test$/}); db.user_sessions.deleteMany({session_token:/^test_session_/}); db.chats.deleteMany({user_id:/^test-user-/}); db.payment_transactions.deleteMany({user_id:/^test-user-/});"
    ], capture_output=True, text=True)


# ---------- Public endpoints ----------
def test_health():
    r = requests.get(f"{API}/health", timeout=10)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_welcome_quote():
    r = requests.get(f"{API}/quotes/welcome", timeout=10)
    assert r.status_code == 200
    j = r.json()
    assert "text" in j and "author" in j and j["text"] and j["author"]


def test_subscription_packages():
    r = requests.get(f"{API}/subscription/packages", timeout=10)
    assert r.status_code == 200
    pkgs = {p["id"]: p for p in r.json()}
    assert pkgs["weekly"]["amount"] == 4.99
    assert pkgs["monthly"]["amount"] == 14.99
    assert pkgs["annual"]["amount"] == 99.99
    assert all(p["currency"] == "usd" for p in pkgs.values())


def test_auth_me_unauthenticated():
    r = requests.get(f"{API}/auth/me", timeout=10)
    assert r.status_code == 401


def test_auth_session_invalid():
    r = requests.post(f"{API}/auth/session", json={"session_id": "bogus_invalid_xyz"}, timeout=15)
    assert r.status_code == 401


# ---------- Auth via seed ----------
def test_auth_me_with_seeded_session():
    token, user_id, email = _seed_user()
    r = requests.get(f"{API}/auth/me", headers=_auth(token), timeout=10)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["user_id"] == user_id
    assert j["email"] == email
    assert j["subscription_status"] == "trial"
    assert "trial_end" in j


def test_subscription_status_trial():
    token, _, _ = _seed_user()
    r = requests.get(f"{API}/subscription/status", headers=_auth(token), timeout=10)
    assert r.status_code == 200
    j = r.json()
    assert j["state"] == "trial"
    assert j["has_access"] is True


# ---------- Chats ----------
def test_create_chat_manage_and_support():
    token, _, _ = _seed_user()
    for mode in ["manage", "support"]:
        r = requests.post(f"{API}/chats", headers=_auth(token), json={"mode": mode}, timeout=10)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["mode"] == mode
        assert j["chat_id"].startswith("chat_")
        assert j["title"]


def test_list_chats_and_max_5_enforcement():
    token, _, _ = _seed_user()
    chat_ids = []
    for i in range(6):
        r = requests.post(f"{API}/chats", headers=_auth(token),
                          json={"mode": "support", "title": f"chat-{i}"}, timeout=10)
        assert r.status_code == 200
        chat_ids.append(r.json()["chat_id"])
        time.sleep(0.05)  # ensure distinct updated_at
    r = requests.get(f"{API}/chats", headers=_auth(token), timeout=10)
    assert r.status_code == 200
    chats = r.json()
    assert len(chats) == 5, f"Expected 5, got {len(chats)}"
    returned_ids = {c["chat_id"] for c in chats}
    assert chat_ids[0] not in returned_ids, "Oldest chat should have been deleted"
    # sorted desc
    times = [c["updated_at"] for c in chats]
    assert times == sorted(times, reverse=True)


def test_get_and_delete_chat():
    token, _, _ = _seed_user()
    r = requests.post(f"{API}/chats", headers=_auth(token), json={"mode": "support"}, timeout=10)
    chat_id = r.json()["chat_id"]
    g = requests.get(f"{API}/chats/{chat_id}", headers=_auth(token), timeout=10)
    assert g.status_code == 200
    assert g.json()["chat_id"] == chat_id
    assert isinstance(g.json()["messages"], list)
    d = requests.delete(f"{API}/chats/{chat_id}", headers=_auth(token), timeout=10)
    assert d.status_code == 200
    g2 = requests.get(f"{API}/chats/{chat_id}", headers=_auth(token), timeout=10)
    assert g2.status_code == 404


def test_crisis_detection_skips_llm():
    token, _, _ = _seed_user()
    r = requests.post(f"{API}/chats", headers=_auth(token), json={"mode": "support"}, timeout=10)
    chat_id = r.json()["chat_id"]
    msg = requests.post(f"{API}/chats/message", headers=_auth(token),
                        json={"chat_id": chat_id, "text": "I want to kill myself"}, timeout=15)
    assert msg.status_code == 200, msg.text
    j = msg.json()
    assert j["crisis_detected"] is True
    content = j["assistant_message"]["content"]
    assert "988" in content
    assert "iCall" in content


def test_send_message_llm():
    token, _, _ = _seed_user()
    r = requests.post(f"{API}/chats", headers=_auth(token), json={"mode": "support"}, timeout=10)
    chat_id = r.json()["chat_id"]
    msg = requests.post(f"{API}/chats/message", headers=_auth(token),
                        json={"chat_id": chat_id, "text": "I'm feeling a bit anxious about work today."},
                        timeout=60)
    if msg.status_code == 503:
        pytest.skip("LLM service unavailable (non-blocking) — error path 503 working")
    assert msg.status_code == 200, msg.text
    j = msg.json()
    assert j["crisis_detected"] is False
    assert j["user_message"]["role"] == "user"
    assert j["assistant_message"]["role"] == "assistant"
    assert len(j["assistant_message"]["content"]) > 0


# ---------- Subscription gating ----------
def test_expired_trial_blocks_chat_create_and_message():
    token, _, _ = _seed_user(trial_offset_seconds=-3600, subscription_status="expired")
    r = requests.post(f"{API}/chats", headers=_auth(token), json={"mode": "support"}, timeout=10)
    assert r.status_code == 402, r.text
    # also message endpoint should 402 — fake chat_id is fine since access check runs first
    m = requests.post(f"{API}/chats/message", headers=_auth(token),
                      json={"chat_id": "chat_doesnotexist", "text": "hello"}, timeout=10)
    assert m.status_code == 402

    s = requests.get(f"{API}/subscription/status", headers=_auth(token), timeout=10)
    assert s.status_code == 200
    assert s.json()["state"] == "expired"
    assert s.json()["has_access"] is False


def test_active_subscription_can_chat():
    token, _, _ = _seed_user(trial_offset_seconds=-3600, subscription_status="active",
                              subscription_end_offset=30*86400, plan="monthly")
    r = requests.post(f"{API}/chats", headers=_auth(token), json={"mode": "manage"}, timeout=10)
    assert r.status_code == 200, r.text
    s = requests.get(f"{API}/subscription/status", headers=_auth(token), timeout=10)
    assert s.json()["state"] == "active"
    assert s.json()["has_access"] is True


# ---------- Stripe checkout ----------
def test_checkout_invalid_package():
    token, _, _ = _seed_user()
    # bypass pydantic literal validation: send unknown id -> FastAPI returns 422; we need 400.
    # To hit our 400 branch, send a value Pydantic accepts but server rejects — N/A here.
    # So check 422 OR 400 (both indicate rejection)
    r = requests.post(f"{API}/payments/checkout", headers=_auth(token),
                      json={"package_id": "nonsense", "origin_url": "https://example.com"}, timeout=15)
    assert r.status_code in (400, 422), r.text


def test_checkout_monthly_creates_session_and_txn():
    token, user_id, _ = _seed_user()
    r = requests.post(f"{API}/payments/checkout", headers=_auth(token),
                      json={"package_id": "monthly", "origin_url": "https://example.com"}, timeout=30)
    if r.status_code >= 500:
        pytest.skip(f"Stripe service issue: {r.status_code} {r.text}")
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["url"].startswith("http")
    assert j["session_id"]
    # Verify DB transaction entry
    out = subprocess.run(["mongosh", "--quiet", "--eval",
        f"use('test_database'); printjson(db.payment_transactions.findOne({{session_id:'{j['session_id']}'}}, {{_id:0}}));"
    ], capture_output=True, text=True, timeout=10)
    assert "initiated" in out.stdout, out.stdout
    assert user_id in out.stdout


# ---------- Logout ----------
def test_logout_clears_session():
    token, _, _ = _seed_user()
    # use a session cookie since logout reads cookie
    s = requests.Session()
    s.cookies.set("session_token", token)
    r = s.post(f"{API}/auth/logout", timeout=10)
    assert r.status_code == 200
    assert r.json()["ok"] is True
    # Token-based bearer should still validate (logout only removes via cookie path)
    # Verify via DB that session is gone
    out = subprocess.run(["mongosh", "--quiet", "--eval",
        f"use('test_database'); print(db.user_sessions.countDocuments({{session_token:'{token}'}}));"
    ], capture_output=True, text=True, timeout=10)
    assert "0" in out.stdout.strip().split("\n")[-1]
