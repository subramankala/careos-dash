# Handoff Status

Last updated: 2026-03-14 UTC

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
- Added deterministic-first short-circuiting for clear high-frequency read intents (`schedule`, `today schedule`, `status`, med count, critical missed) so `openclaw_first` mode no longer misroutes them through the LLM/delegate path.
- Added graceful caregiver-facing fallback text when Care-Dash link issuance is temporarily unavailable, instead of bubbling up a 500.
- Added `CAREOS_GATEWAY_DASHBOARD_BASE_URL` so the gateway can call Care-Dash `POST /generate-view`.

Key files:

- `/home/kumarmankala/careos/careos/gateway/intent_parser.py`
- `/home/kumarmankala/careos/careos/gateway/careos_adapter.py`
- `/home/kumarmankala/careos/careos/gateway/routes/twilio_gateway.py`
- `/home/kumarmankala/careos/tests/test_gateway_intent_parser.py`
- `/home/kumarmankala/careos/tests/test_gateway_careos_adapter.py`
- `/home/kumarmankala/careos/tests/test_gateway_openclaw_first.py`

### 2d. Structured write confirmation flow started

- Added a first confirmation-based structured action path for natural-language writes.
- Generalized the write proposal path from walk-specific handling to a broader `create_task` schema.
- Current supported slices:
  - `Add evening walk for today`
  - `I need to get calcium score test done over the next 2 days`
  - gateway proposes a structured confirmation
  - user replies `YES` or `CANCEL`
  - on `YES`, CareOS creates the task in the active care plan
- Added a lightweight in-memory pending-action store in the gateway.
- Added active care plan lookup route so the gateway can resolve where to write the confirmed action.

Key files:

- `/home/kumarmankala/careos/careos/gateway/action_proposals.py`
- `/home/kumarmankala/careos/careos/gateway/routes/twilio_gateway.py`
- `/home/kumarmankala/careos/careos/gateway/careos_adapter.py`
- `/home/kumarmankala/careos/careos/api/routes/internal.py`
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
  - `careos`: `20 passed` via `./.venv/bin/pytest tests/test_gateway_intent_parser.py tests/test_gateway_openclaw_first.py`
- Structured action confirmation tests:
  - `careos`: `22 passed` via `./.venv/bin/pytest tests/test_gateway_openclaw_first.py tests/test_gateway_intent_parser.py`
- Generalized create-task parser hardening tests:
  - `careos`: `24 passed` via `./.venv/bin/pytest tests/test_gateway_openclaw_first.py tests/test_gateway_intent_parser.py`
- Live VM verification:
  - local `http://127.0.0.1:8000/health` returns OK
  - public `https://dash.theginger.ai/health` returns OK
  - public `https://careos.theginger.ai/gateway/twilio/webhook` returns a signed dashboard link for caregiver dashboard intent
  - broader public phrase `how is my patient doing` also returns a signed dashboard link
  - public phrase `what's today's schedule` now returns the schedule instead of `Missed critical wins today`
- Live services restarted after structured action flow implementation:
  - `careos-lite-api`
  - `careos-lite-gateway`
- Live public structured proposal verification:
  - `I need to get calcium score test done over the next 2 days`
  - response: structured confirmation with `YES` / `CANCEL`
- Live public end-to-end create verification:
  - `I need to get calcium score test done over the next 2 days`
  - `YES`
  - response: `Created calcium score test. You can ask for your dashboard to verify it.`
- Live public end-to-end complete verification:
  - `I got the calcium score test done`
  - `YES`
  - response: `Marked calcium score test as completed.`
  - CareOS timeline verification: one `Calcium score test` instance moved from `pending` to `completed`
- Live public end-to-end update verification:
  - first attempt exposed the bug in the old `delay_win` strategy:
    - cross-day walk move disappeared from visible timelines
    - same-day recurring med move duplicated the task
  - after Slice 1 fix:
    - `Add evening walk for today` -> `YES` created a fresh one-off walk
    - `Move my walk to tomorrow morning` -> `YES`
    - response: `Moved evening walk. You can ask for your schedule to verify it.`
    - verification: walk disappeared from today's timeline and appeared on `2026-03-15` at `03:30:00Z` (`9:00 AM` patient local time)
 - Planner/compiler separation verification:
   - focused planner and gateway tests passed: `34 passed`
   - pending confirmation survived a `careos-lite-gateway` restart
- Legacy ingress restoration verification:
  - focused gateway/planner/parser suite passed: `40 passed`
  - live public `whoami` returns caregiver identity and active patient
  - live public `next` returns the next timeline item
  - live public `help` returns the legacy command list
  - live public `patients` now returns `Active patient: Nageswara Rao (Asia/Kolkata).` for single-patient contexts instead of falling through to planner/status behavior
  - live public `today` now returns the richer legacy schedule output with PRN/SOS items
  - live public `done b7d09d8c` returned `Marked b7d09d8c as completed.`
  - timeline verification showed `b7d09d8c-7f9a-43b7-a02f-d481babf3243` changed from `due` to `completed`
 - Clarification prompt improvement verification:
   - focused suite passed: `42 passed`
   - live ambiguous request `Move my Dytor 5mg to evening` now returns:
     - `I found multiple matches for dytor 5mg: Dytor 5mg at 10:30 AM (medication, pending); Dytor 5mg at 12:30 PM (medication, delayed). Reply with the time or item number you mean, or ask for your schedule first.`
 - Setup shortcut verification:
   - focused suite passed: `45 passed`
   - vague create intents now enter the existing setup wizard:
     - `Add a medication`
     - `Add an appointment`
     - `Add a routine`
   - live local `Add a medication` returned `Medication name?`
   - subsequent public probe for the same sender returned `Medication timing? Use HH:MM (24h).`, confirming the wizard session remained active and advanced correctly
 - Setup control verification:
   - gateway-path setup tests passed: `4 passed`
   - live `restart setup` returned the full care setup menu
   - live `cancel setup` returned a clean exit message
   - live `Add a medication` after `cancel setup` returned `Medication name?`, confirming reset worked

### 7. Planner durability and safer binding

- Added explicit planner stages:
  - `ParsedAction`
  - `BoundAction`
  - `CompiledActionPlan`
- Pending confirmations now persist through CareOS internal API routes and survive gateway restarts.
- Binding now carries explicit status and returns clarification instead of creating an executable pending action when the target is ambiguous.
- Clarification prompts now include candidate-aware details:
  - local time
  - category
  - current state
  - explicit follow-up instruction to reply with time or item number

Key files:

- `/home/kumarmankala/careos/careos/gateway/action_planner.py`
- `/home/kumarmankala/careos/careos/gateway/routes/twilio_gateway.py`
- `/home/kumarmankala/careos/careos/api/routes/internal.py`

### 8. Legacy gateway command and onboarding restoration

- Restored legacy ingress behavior in the live single-webhook gateway for:
  - `whoami`
  - `profile`
  - `next`
  - `help`
  - `patients`
  - `switch`
  - `use <n>`
- Restored strict deterministic passthrough for exact legacy command forms:
  - `schedule`
  - `today`
  - `status`
  - `done <item_no|win_id_prefix>`
  - `skip <item_no|win_id_prefix>`
  - `delay <item_no|win_id_prefix> <minutes>`
- Reconnected onboarding handling at the gateway edge using `app_context.onboarding`.
- Added explicit single-patient handling for `patients` / `switch` so those commands now return the active linked patient instead of falling through to the planner path.
- Added setup shortcuts for vague create intents so the gateway can start the existing onboarding/setup wizard when a message is underspecified:
  - `Add a medication`
  - `Add an appointment`
  - `Add a routine`
- Added explicit setup control commands in the shared onboarding service:
  - `restart setup`
  - `setup menu`
  - `cancel setup`
  - `cancel wizard`

Key files:

- `/home/kumarmankala/careos/careos/gateway/routes/twilio_gateway.py`
- `/home/kumarmankala/careos/tests/test_gateway_openclaw_first.py`

### 9. Reference guides added

- Added a technical guide for architects and engineers covering the live architecture, flows, planner model, operational notes, and known constraints.
- Added an end-user guide covering WhatsApp commands, dashboard access, natural-language writes, setup wizard usage, and recovery commands.

Guide files:

- `/home/kumarmankala/careos-dash/docs/technical_implementation_guide.md`
- `/home/kumarmankala/careos-dash/docs/end_user_guide.md`
  - recurring override slice:
    - `Move my Ecosprin 75mg to evening` -> `YES`
    - response: `Moved ecosprin 75mg. You can ask for your schedule to verify it.`
    - verification: original morning `Ecosprin 75mg` occurrence disappeared and a new one-off `Ecosprin 75mg` appeared at `2026-03-14T12:30:00Z` (`6:00 PM` patient local time)
    - recurring reschedules now use `create one-off replacement + supersede original occurrence`
- Generalized proposal coverage now includes:
  - appointments, e.g. `Schedule cardiology appointment tomorrow morning`
  - medication reminders, e.g. `Remind me to take atorvastatin tomorrow evening`
  - complete-task confirmations, e.g. `I got the calcium score test done`
  - instance-level reschedule confirmations, e.g. `Move my walk to tomorrow morning`
- Intent parser now avoids routing create-like `tomorrow` / `schedule` messages into read intents before the proposal layer can handle them.
- Diagnostic and LLM-backed task proposals now round start times forward, so confirmed writes do not fail validation with past `scheduled_start` values.
- `update_task` for one-off tasks now compiles to a real care-plan definition edit using `win_definition_id` lookup and `PATCH /care-plans/{care_plan_id}/wins/{win_definition_id}`.
- `complete_task` resolves against the current timeline and executes via `complete_win`.
- recurring `update_task` now compiles to a one-off override:
  - create replacement task at the requested time
  - supersede the original recurring instance
- planner layer added:
  - parse -> bind -> compile -> execute stages are now explicit in the gateway
  - gateway pending state stores a compiled action plan rather than a raw proposal
- durable pending confirmation persistence added:
  - compiled plans are persisted through CareOS internal API endpoints
  - gateway can recover pending confirmations after process restart
- safer binding slice added:
  - planner now tracks binding status explicitly
  - ambiguous target matches compile to a clarification response instead of a pending executable plan
- Current conclusion:
  - `complete_task` is viable on live data
  - `update_task` is now viable for one-off tasks
  - recurring-task rescheduling now has a working first implementation via one-off override + supersede
  - planner/compiler-style staging is now in place, though parsing and binding are still partly heuristic
  - pending confirmations now survive gateway restarts
  - target binding is safer because ambiguous matches no longer auto-execute

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

1. Continue separating parsing from binding inside the planner so target selection uses richer candidate scoring and explicit clarification prompts.
2. Clean up previously incorrect recurring-item mutations created before the override fix, if desired.
3. Add stronger retry/backoff and failure classification in `app/services/careos_client.py`.
4. Decide whether pending plan persistence should stay on reused session storage or move to a dedicated table.

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
