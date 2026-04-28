# Auth Testing Playbook (Emergent Google OAuth)

This app uses Emergent-managed Google OAuth.

## Backend route map
- POST /api/auth/session — exchanges Emergent `session_id` (URL fragment) for our `session_token` (httpOnly cookie + 7-day DB-stored session). Body: `{ "session_id": "..." }`
- GET  /api/auth/me — returns current user (cookie OR `Authorization: Bearer <session_token>`).
- POST /api/auth/logout — clears cookie and DB session.

## How testing agent should bypass the OAuth flow
Real Google OAuth cannot run in CI. To test protected routes, seed a fake session directly:

```bash
mongosh --eval "
use('test_database');
var userId = 'test-user-' + Date.now();
var token = 'test_session_' + Date.now();
var now = new Date();
var trialEnd = new Date(now.getTime() + 24*60*60*1000);
db.users.insertOne({
  user_id: userId,
  email: 'tester+' + Date.now() + '@mindmanage.test',
  name: 'Test User',
  picture: null,
  created_at: now.toISOString(),
  trial_end: trialEnd.toISOString(),
  subscription_status: 'trial',
  subscription_plan: null,
  subscription_end: null
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: token,
  expires_at: new Date(now.getTime() + 7*24*60*60*1000).toISOString(),
  created_at: now.toISOString()
});
print('TOKEN=' + token);
print('USER_ID=' + userId);
"
```

Then for backend API tests use:
```bash
curl -H "Authorization: Bearer $TOKEN" $API/api/auth/me
```

## To test an EXPIRED-trial user (subscription gating)
Create the user with `trial_end` set to a past date:
```js
trialEnd = new Date(now.getTime() - 1000);
```
The /api/chats POST and /api/chats/message routes should return 402.

## To test an ACTIVE-subscriber
Set `subscription_end` to a future date and `subscription_status: 'active'`.

## Cleanup
```bash
mongosh --eval "
use('test_database');
db.users.deleteMany({email: /@mindmanage\.test$/});
db.user_sessions.deleteMany({session_token: /^test_session_/});
db.chats.deleteMany({user_id: /^test-user-/});
db.payment_transactions.deleteMany({user_id: /^test-user-/});
"
```
