# Caregiver Dashboard MVP Spec

## User journey

1. Caregiver sends `show caregiver dashboard`.
2. Twilio posts the message to OpenClaw ingress.
3. OpenClaw resolves caregiver identity and active authorization grant.
4. OpenClaw generates a signed, expiring dashboard URL.
5. Caregiver opens the link.
6. Care-Dash validates token and revalidates live authorization before rendering.

## Scope

- Read-only caregiver dashboard
- Signed expiring links
- Mocked CareOS data client
- Mocked authorization grant store
- Mobile-friendly HTML dashboard

## Out of scope

- Patient dashboard
- Clinician editing
- Broad clinical NLP
- Native app flow
- Real DB-backed auth

## Dashboard sections

- Patient summary
- Active escalations
- Medication adherence snapshot
- Recent timeline
- Criticality legend
- Quick actions
- Access scope summary

## Security requirements

- Reject invalid tokens
- Reject expired tokens
- Reject revoked or version-mismatched grants
- Never trust patient identity from URL parameters
