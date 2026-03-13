# Handoff Status

Last updated: 2026-03-13 UTC

## Repos and backups

- Active repo: `/home/kumarmankala/careos-dash`
- Backup of `careos`: `/home/kumarmankala/backups/careos-20260313T100418Z`
- Backup of `careos-dash`: `/home/kumarmankala/backups/careos-dash-20260313T100418Z`

## Target architecture

The implementation is being aligned to:

`Twilio -> OpenClaw -> MCP/CareOS -> Care-Dash`

Current repo responsibility:

- `careos-dash` is the MVP implementation target.
- `POST /twilio/inbound` is treated as the OpenClaw ingress point for this MVP.
- `POST /generate-view` is the internal OpenClaw link issuance path.
- `GET /v/{token}` is the Care-Dash rendering surface.

## Completed work

### 1. Safety and auth hardening

- Added explicit actor-to-patient grant model in mock data.
- Added `authorization_version` to signed tokens.
- Added live authorization revalidation on `GET /v/{token}`.
- Added `error_unauthorized.html`.

Key files:

- `app/services/authorization_service.py`
- `app/security.py`
- `app/routes/views.py`
- `data/mock_data.py`

### 2. Architecture split inside repo

- Introduced `OpenClawIngressService` so ingress/link issuance is separated from dashboard rendering.
- Kept rendering logic in `DashboardService` and `views.py`.

Key files:

- `app/services/openclaw_ingress_service.py`
- `app/routes/twilio.py`
- `app/routes/internal.py`
- `app/routes/views.py`

### 2b. Single-webhook dashboard dispatch in CareOS gateway

- Kept Twilio on a single inbound webhook at `POST /gateway/twilio/webhook`.
- Added a gateway-level `caregiver_dashboard` intent that routes dashboard-like requests to Care-Dash link issuance.
- Added broader dashboard phrase recognition, including patient-summary wording and typo-tolerant `dashboard` matching.
- Added pre-LLM dashboard short-circuiting so obvious caregiver-dashboard requests are routed deterministically before any LLM misclassification.
- Added graceful caregiver-facing fallback text when Care-Dash link issuance is temporarily unavailable, instead of bubbling up a 500.
- Added `CAREOS_GATEWAY_DASHBOARD_BASE_URL` so the gateway can call Care-Dash `POST /generate-view`.

Key files:

- `/home/kumarmankala/careos/careos/gateway/intent_parser.py`
- `/home/kumarmankala/careos/careos/gateway/careos_adapter.py`
- `/home/kumarmankala/careos/careos/gateway/routes/twilio_gateway.py`
- `/home/kumarmankala/careos/tests/test_gateway_intent_parser.py`
- `/home/kumarmankala/careos/tests/test_gateway_careos_adapter.py`
- `/home/kumarmankala/careos/tests/test_gateway_openclaw_first.py`

### 2c. VM deployment completed

- Installed and started `careos-dash` as a systemd service on port `8000`.
- Replaced the invalid `careos-dash/.env` scratch file with a valid runtime env.
- Pointed Care-Dash public links to `https://dash.theginger.ai`.
- Configured the CareOS gateway with `CAREOS_GATEWAY_DASHBOARD_BASE_URL=http://127.0.0.1:8000`.
- Restarted live services:
  - `careos-dash`
  - `careos-lite-gateway`
  - `careos-lite-api`
  - `careos-lite-mcp`
- Confirmed:
  - `https://dash.theginger.ai/health` returns healthy
  - `https://careos.theginger.ai/gateway/twilio/webhook` now returns a signed Care-Dash link for `show caregiver dashboard`

Key files:

- `/home/kumarmankala/careos-dash/deploy/systemd/careos-dash.service`
- `/home/kumarmankala/careos-dash/.env`
- `/home/kumarmankala/careos/.env`

### 3. MCP-shaped CareOS contract

- Replaced the older generic mock client with `MockCareOSMCPClient`.
- Authorization and dashboard aggregation now depend on this contract instead of reading mock data directly from multiple layers.
- Added a real MCP-backed adapter path with mock fallback.
- Added CareOS MCP tool coverage for dashboard-oriented reads.
- Fixed MCP query encoding for phone numbers containing `+` so caregiver context resolution works against a live server.
- Added retry/backoff behavior to the MCP client for transient transport and server errors.
- Wired richer CareOS patient profile fields through the dashboard contract:
  - `primary_language`
  - `persona_type`
  - `risk_level`
  - `status`

Key file:

- `app/services/careos_client.py`

### 4. Section-level scope enforcement

- Dashboard now exposes explicit `section_visibility`.
- Added a downgraded caregiver grant that can view dashboard + criticality only.
- Templates show access-limited messages for hidden sections.
- Dashboard header and summary cards now render richer patient-profile metadata from CareOS.

Key files:

- `app/services/dashboard_service.py`
- `app/templates/caregiver_dashboard.html`
- `data/mock_data.py`

### 5. Structured logging

- Added structured JSON logging helpers.
- Link issuance/rejection is logged.
- Dashboard access granted/denied is logged.

Key files:

- `app/logging.py`
- `app/services/openclaw_ingress_service.py`
- `app/routes/views.py`

### 6. Verification

- Replaced hanging `TestClient`-style tests with route-level tests because in-process ASGI HTTP execution hangs in this environment even for a minimal FastAPI app.
- Current focused suite passes:
  - `tests/test_careos_client.py`
  - `tests/test_security.py`
  - `tests/test_generate_view.py`
  - `tests/test_authorization.py`
  - `tests/test_dashboard_render.py`
  - `tests/test_twilio_inbound.py`
  - `tests/test_intent_parser.py`
- Last known result: `12 passed in 2.58s`
- Updated results:
  - `careos-dash`: `15 passed in 4.03s`
  - `careos`: `tests/test_mcp_server.py` passes after converting to direct route tests
- `python3 -m py_compile app/*.py app/routes/*.py app/services/*.py data/*.py tests/*.py` passes.
- Live in-memory validation also succeeded against freshly started CareOS API + MCP servers, including:
  - `careos_resolve_caregiver_context`
  - `careos_get_view_access`
  - `careos_get_patient_summary`
  - `careos_get_escalations`
  - `careos_get_medications`
  - `careos_get_recent_events`
  - `careos_get_task_criticality`
- Latest repo-local venv test results:
  - `careos-dash`: `15 passed in 5.82s` via `./.venv/bin/pytest`
  - `careos`: `7 passed` via `./.venv/bin/pytest tests/test_mcp_server.py`
- Gateway dispatcher tests:
  - `careos`: `11 passed` via `./.venv/bin/pytest tests/test_gateway_intent_parser.py tests/test_gateway_careos_adapter.py tests/test_gateway_openclaw_first.py`
- Gateway parser hardening tests:
  - `careos`: `12 passed` via `./.venv/bin/pytest tests/test_gateway_intent_parser.py tests/test_gateway_openclaw_first.py`
- Live VM verification:
  - local `http://127.0.0.1:8000/health` returns OK
  - public `https://dash.theginger.ai/health` returns OK
  - public `https://careos.theginger.ai/gateway/twilio/webhook` returns a signed dashboard link for caregiver dashboard intent
  - broader public phrase `how is my patient doing` also returns a signed dashboard link

## Important local issue

`/home/kumarmankala/careos-dash/.env` contains a malformed line and triggers:

`python-dotenv could not parse statement starting at line 6`

This was left untouched because it appears to be local user config, not source code. If another Codex needs a cleaner runtime, inspect and fix `.env` manually.

## Current code status

Git status in `careos-dash` shows uncommitted changes only in this repo. No commit has been made.

## Recommended next steps

### Next implementation slice

Move from adapter implementation to integration hardening and richer real-data coverage.

Priority order:

1. Verify additional live WhatsApp caregiver phrases through Twilio and confirm expected product wording.
2. Add stronger retry/backoff and failure classification in `app/services/careos_client.py`.
3. Replace remaining placeholder fields such as age, sex, primary conditions, and last check-in once CareOS exposes them directly.
4. Clean up the unrelated pre-existing syntax issue in `careos/careos/gateway/openclaw_client.py` when ready.

### Constraints to preserve

- Twilio stays transport only.
- OpenClaw owns ingress/link issuance.
- CareOS owns truth and authorization-worthy data.
- Care-Dash stays presentation-only.
- Signed URL validity alone is never sufficient.

## Useful files for the next Codex

- `README.md`
- `docs/careos_openclaw_architecture_spec.md`
- `docs/careos_caregiver_dashboard_mvp_spec.md`
- `app/services/openclaw_ingress_service.py`
- `app/services/careos_client.py`
- `app/services/dashboard_service.py`
- `app/services/authorization_service.py`
- `tests/test_authorization.py`
- `tests/test_dashboard_render.py`
