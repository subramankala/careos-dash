# Ginger Care-Dash

Ginger Care-Dash is a FastAPI MVP for the secure caregiver dashboard surface in a Twilio -> OpenClaw -> MCP/CareOS -> Care-Dash flow.

## What it does

- Caregiver sends a WhatsApp message such as `show caregiver dashboard`
- Twilio posts that message to `POST /twilio/inbound`, which acts as the OpenClaw ingress point in this MVP
- OpenClaw resolves the caregiver's mocked patient mapping and active authorization grant
- OpenClaw generates a signed, expiring URL
- Caregiver opens `GET /v/{token}` in a browser
- Care-Dash validates the token, revalidates live authorization, and renders a mobile-friendly caregiver dashboard

## Architecture summary

`Caregiver -> WhatsApp -> Twilio -> OpenClaw ingress -> mocked MCP/CareOS client -> signed URL generator -> Care-Dash web view`

MVP boundaries:

- Twilio is transport only
- OpenClaw owns message handling, caregiver resolution, and signed-link issuance
- CareOS data and authorization truth are mocked behind service interfaces
- A real MCP-backed CareOS adapter can be enabled, with mock fallback preserved for local work
- Care-Dash renders the secure browser view
- Signed URLs are necessary but not sufficient; live authorization is revalidated at page load

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
    authorization_service.py
    careos_client.py
    openclaw_ingress_service.py
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
    error_unauthorized.html
  static/
    app.css
data/
  mock_data.py
docs/
  careos_openclaw_architecture_spec.md
  careos_caregiver_dashboard_mvp_spec.md
tests/
  test_careos_client.py
  test_authorization.py
  test_security.py
  test_generate_view.py
  test_dashboard_render.py
  test_intent_parser.py
```

## Setup

```bash
cd /home/kumarmankala/careos-dash
python3 -m venv .venv
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
- `GINGER_CAREOS_DASH_OPENCLAW_NAME`
- `GINGER_CAREOS_DASH_USE_REAL_MCP`
- `GINGER_CAREOS_DASH_MCP_BASE_URL`
- `GINGER_CAREOS_DASH_MCP_API_KEY`

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
- Expired, invalid, or no-longer-authorized links render clean error pages
- Live caregiver grant revalidation happens on `GET /v/{token}`
- The repo includes a real MCP-backed adapter with mock fallback, so local MVP work still runs without a live CareOS MCP service
- MVP does not yet implement:
  - Twilio signature validation
  - audit logging
  - DB-backed grant store
  - production-ready MCP retry/backoff and circuit breaking

## Future roadmap

- Replace fallback-first MCP usage with production MCP as the default path
- Add patient and clinician dashboards
- Add server-side audit log for signed link usage
- Add one-time-use or revocable tokens
- Add real Twilio signature verification
- Add role-aware dashboard access beyond caregiver view
