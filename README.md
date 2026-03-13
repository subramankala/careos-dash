# Ginger CareOS Dash

Ginger CareOS Dash is a FastAPI MVP for secure caregiver dashboard links triggered from WhatsApp.

## What it does

- Caregiver sends a WhatsApp message such as `show caregiver dashboard`
- Twilio posts that message to `POST /twilio/inbound`
- Backend resolves the caregiver's mocked patient mapping
- Backend generates a signed, expiring URL
- Caregiver opens `GET /v/{token}` in a browser
- Server validates the token and renders a mobile-friendly caregiver dashboard

## Architecture summary

`Caregiver -> WhatsApp -> Twilio webhook -> intent parser -> CareOS data client -> signed URL generator -> secure mobile web dashboard`

MVP boundaries:

- Twilio is transport only
- This app is the secure dashboard/link service
- CareOS data is mocked behind a simple client interface
- Signed URLs act as bearer access for short-lived dashboard viewing

## Project structure

```text
app/
  main.py
  config.py
  models.py
  schemas.py
  security.py
  intent.py
  dependencies.py
  services/
    careos_client.py
    url_service.py
    twilio_service.py
    dashboard_service.py
  routes/
    twilio.py
    views.py
    internal.py
  templates/
    base.html
    caregiver_dashboard.html
    error_invalid_link.html
    error_expired_link.html
  static/
    app.css
data/
  mock_data.py
tests/
  test_security.py
  test_generate_view.py
  test_dashboard_render.py
  test_intent_parser.py
```

## Setup

```bash
cd /Users/kumarmankala/code/Codex/Wellness-check/careos-dash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment variables

Copy `.env.example` to `.env` if you want to override defaults.

- `GINGER_CAREOS_DASH_HOST`
- `GINGER_CAREOS_DASH_PORT`
- `GINGER_CAREOS_DASH_BASE_URL`
- `GINGER_CAREOS_DASH_SIGNING_SECRET`
- `GINGER_CAREOS_DASH_LINK_EXPIRY_SECONDS`

## Run locally

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Health check

```bash
curl -s http://127.0.0.1:8000/health
```

## Test Twilio webhook locally

```bash
curl -s -X POST http://127.0.0.1:8000/twilio/inbound \
  -d "From=+14085157095" \
  -d "To=+14155238886" \
  -d "Body=show caregiver dashboard" \
  -d "MessageSid=SM_test_001"
```

Expected response shape:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>Open caregiver dashboard: http://localhost:8000/v/&lt;token&gt; (expires in 30 minutes)</Message>
</Response>
```

## Example generate-view request

```bash
curl -s -X POST http://127.0.0.1:8000/generate-view \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant_001",
    "patient_id": "patient_123",
    "actor_id": "caregiver_999",
    "role": "caregiver",
    "view": "caregiver_dashboard"
  }'
```

Example response:

```json
{
  "url": "http://localhost:8000/v/<token>",
  "expires_in_seconds": 1800
}
```

## Run tests

```bash
pytest -q
```

## Security notes

- Tokens are signed server-side with `PyJWT` using `HS256`
- Token contains only authorization context, never raw medical data
- URL query tampering is prevented because access comes only from signed claims
- Expired and invalid tokens render clean error pages
- MVP does not yet implement:
  - Twilio signature validation
  - jti revocation storage
  - audit logging
  - real CareOS API integration
  - database-backed identity mapping

## Future roadmap

- Replace mock CareOS client with real API client
- Add patient and clinician dashboards
- Add server-side audit log for signed link usage
- Add one-time-use or revocable tokens
- Add real Twilio signature verification
- Add role-aware dashboard access beyond caregiver view
