# Ginger CareOS / OpenClaw Architecture Spec

## Core flow

`Caregiver -> Twilio -> OpenClaw -> MCP/CareOS client -> CareOS -> signed URL -> Care-Dash`

## Boundary rules

- Twilio is transport only.
- OpenClaw owns inbound message interpretation, caregiver resolution, authorization checks, and signed URL issuance.
- CareOS owns clinical truth, caregiver authorization truth, criticality definitions, and care-plan data.
- Care-Dash is a secure browser-rendered presentation surface only.

## MVP alignment

- `POST /twilio/inbound` is treated as the OpenClaw ingress point.
- `POST /generate-view` is the internal signed-link issuance path.
- `GET /v/{token}` is the Care-Dash view surface.
- URL tokens contain authorization context only and are revalidated against the live caregiver grant before rendering.

## Authorization model

- Caregiver identity resolution is not sufficient for access.
- Every caregiver view requires an active actor-to-patient authorization grant.
- Signed URLs include `authorization_version`.
- Revoked or version-mismatched grants fail at page load.

## Policy taxonomy

Only these criticality enums are allowed:

- `NON_NEGOTIABLE`
- `FLEXIBLE_CLINICAL`
- `OPTIONAL_LIFESTYLE`
