# Technical Implementation Guide

## Audience

This guide is for architects, backend engineers, frontend engineers, and operators working on the live CareOS / OpenClaw / Care-Dash system.

## Current live architecture

The deployed architecture is:

`Twilio / WhatsApp -> CareOS Gateway (OpenClaw-style ingress) -> CareOS APIs / MCP -> Care-Dash`

Current role split:

- `Twilio` is transport only.
- `careos` gateway is the single inbound webhook and the conversational ingress/orchestration layer.
- `careos` core services remain the clinical source of truth and own care-plan and win data.
- `careos-dash` is the secure caregiver web surface.

## Public endpoints

Live routes:

- Twilio webhook: `https://careos.theginger.ai/gateway/twilio/webhook`
- Care-Dash base URL: `https://dash.theginger.ai`
- Care-Dash health: `https://dash.theginger.ai/health`

Internal service split:

- `careos-lite-gateway` serves the single webhook and conversational planner path.
- `careos-lite-api` serves CareOS APIs and internal routes.
- `careos-lite-mcp` exposes MCP-style tool access for dashboard reads.
- `careos-dash` serves signed-link rendering and caregiver dashboard pages.

## Main request flows

### 1. Caregiver dashboard flow

1. Caregiver sends a dashboard-like WhatsApp message.
2. Gateway classifies it as `caregiver_dashboard`.
3. Gateway calls Care-Dash link issuance.
4. Care-Dash generates a signed link with `authorization_version`.
5. Caregiver opens `/v/{token}`.
6. Care-Dash revalidates authorization live before rendering.

Important property:

- link validity alone is not enough; authorization is rechecked at render time.

### 2. Deterministic legacy command flow

Exact command forms bypass the planner and route to the legacy deterministic router:

- `schedule`
- `today`
- `status`
- `next`
- `whoami`
- `profile`
- `help`
- `patients`
- `switch`
- `use <n>`
- `done <item_no|win_id_prefix>`
- `skip <item_no|win_id_prefix>`
- `delay <item_no|win_id_prefix> <minutes>`

This preserves older reliable operational behavior while allowing richer language elsewhere.

### 3. Natural-language write flow

For write-like requests, the gateway now uses a planner pipeline:

`parse -> bind -> compile -> execute`

Current supported classes:

- `create_task`
- `complete_task`
- `update_task`

Examples:

- `Add evening walk for today`
- `I need to get calcium score test done over the next 2 days`
- `I got the calcium score test done`
- `Move my walk to tomorrow morning`

Behavior:

1. User sends natural-language request.
2. Gateway produces a structured proposal.
3. For writes, the user must confirm with `YES` or `CANCEL`.
4. Gateway executes the compiled CareOS action only after confirmation.

### 4. Setup wizard flow

Underspecified create intents are routed into the shared setup wizard instead of being silently ignored.

Supported setup shortcuts:

- `Add a medication`
- `Add an appointment`
- `Add a routine`

Setup control commands:

- `restart setup`
- `setup menu`
- `cancel setup`
- `cancel wizard`

## Planner and semantic model

The current planner is compiler-like, but not yet a full AST system.

Current internal objects:

- `ParsedAction`
- `BoundAction`
- `CompiledActionPlan`

Important design choice:

- deterministic reads and exact legacy commands remain deterministic-first
- natural-language mutations use structured interpretation plus confirmation

This keeps high-frequency operational reads boringly reliable while letting writes be more expressive.

## Binding and ambiguity handling

Target resolution is explicit.

Binding statuses currently include:

- `not_required`
- `bound`
- `not_found`
- `ambiguous`

For ambiguous target matches:

- the system does not create an executable pending action
- it returns a clarification prompt instead

Example:

- `Move my Dytor 5mg to evening`

returns a candidate-aware clarification with local times and states, such as:

- `Dytor 5mg at 10:30 AM (medication, pending)`
- `Dytor 5mg at 12:30 PM (medication, delayed)`

## CareOS execution semantics

Current write execution strategies:

- `create_task`
- `complete_task`
- `reschedule_one_off_task`
- `override_recurring_task`

Important implementation detail:

- recurring reschedules do not mutate the recurring definition directly for a single occurrence
- they create a one-off replacement and supersede the original occurrence

This was introduced because naive `delay_win` behavior caused disappearing or duplicated items.

## Pending confirmation durability

Pending confirmations are durable across gateway restarts.

Implementation:

- pending compiled plans are serialized
- stored through CareOS internal routes
- recovered by the gateway on restart

Operational effect:

- a user can receive a confirmation prompt
- gateway can restart
- the later `YES` still completes the intended mutation

## Care-Dash security model

Care-Dash currently implements:

- signed dashboard links
- explicit caregiver authorization model
- `authorization_version` in link claims
- live authorization revalidation on page load
- section-level visibility enforcement

Dashboard access is therefore:

- token-validated
- authorization-validated
- scope-filtered

## MCP and data contracts

Care-Dash uses an MCP-shaped CareOS client with real adapter support and mock fallback.

Current data reads include:

- caregiver context resolution
- authorization grant lookup
- patient summary
- escalations
- medications
- recent events
- task criticality

## Operational notes

Live services to be aware of:

- `careos-lite-api`
- `careos-lite-gateway`
- `careos-lite-mcp`
- `careos-dash`

Common deployment action after gateway changes:

- restart `careos-lite-gateway`

Common deployment action after API / MCP changes:

- restart `careos-lite-api`
- restart `careos-lite-mcp`

## Known testing limitation

The older `TestClient`-based onboarding tests are still prone to hanging in this environment.

Practical workaround used so far:

- route-level or focused tests for changed slices
- live webhook probes for final verification

## Recommended next work

1. Add candidate scoring so the planner can rank likely targets before asking for clarification.
2. Improve multi-turn clarification so users can answer with just `morning one` or `the delayed one`.
3. Continue hardening MCP/client retry classification and upstream error handling.
4. Extend the same structured planner model to more preference and policy mutations.
