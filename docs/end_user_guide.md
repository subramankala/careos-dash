# End User Guide

## What this system does

You can use WhatsApp to:

- check today’s schedule
- ask for your caregiver dashboard
- mark tasks done
- move or reschedule some tasks
- add medications, appointments, and routines

## WhatsApp number behavior

Send messages to the same CareOS WhatsApp number you already use.

The system understands two kinds of requests:

- exact commands like `schedule`, `next`, `whoami`
- natural-language requests like `show caregiver dashboard` or `add evening walk for today`

## Common commands

These work as direct commands:

- `schedule`
- `today`
- `next`
- `status`
- `whoami`
- `help`
- `patients`
- `switch`
- `use 1`
- `done 3`
- `skip 2`
- `delay 4 30`

Examples:

- `done 3`
- `delay 2 15`
- `use 2`

## Caregiver dashboard

You can ask for the dashboard with messages like:

- `show caregiver dashboard`
- `give me the patient summary`
- `show patient status`
- `how is my patient doing`

You will receive a secure dashboard link.

## Adding things with natural language

You can create some tasks using natural language.

Examples:

- `Add evening walk for today`
- `I need to get calcium score test done over the next 2 days`
- `Schedule cardiology appointment tomorrow morning`
- `Remind me to take atorvastatin tomorrow evening`

For these requests, the system usually sends a confirmation first.

Reply with:

- `YES` to continue
- `CANCEL` to stop

## Setup wizard

If your request is too vague, the system may start a setup wizard instead.

These messages start the wizard:

- `Add a medication`
- `Add an appointment`
- `Add a routine`

Example medication flow:

1. `Add a medication`
2. system: `Medication name?`
3. you: `Pantoprazole 40mg`
4. system: `Medication timing? Use HH:MM (24h).`
5. you: `08:00`

The wizard will continue asking for the remaining details.

## If you get stuck in setup

Use these commands:

- `restart setup`
- `setup menu`
- `cancel setup`
- `cancel wizard`

What they do:

- `restart setup` or `setup menu` takes you back to the setup menu
- `cancel setup` exits the wizard completely

Example:

If you send `Add a medication` and later get:

- `Invalid time. Use HH:MM (24h).`

that means the wizard is already waiting for a time.

You can either:

- send a valid time like `08:00`
- or send `cancel setup` and start again

## If the system asks a clarification question

Sometimes the system finds more than one matching task.

Example:

- `Move my Dytor 5mg to evening`

If there are multiple matching items, the system may reply with a list of options and their times.

Then you should reply with:

- the time
- or the item number
- or ask for `schedule`

## Tips

- Use exact commands when you want something fast and reliable.
- Use natural language when you want to create or change something.
- If a setup flow feels stuck, use `cancel setup`.
- If you are unsure what is available, send `help`.

## Safety note

Some changes require confirmation before they are applied.

When you see a message ending with:

- `Reply YES to confirm or CANCEL.`

nothing has been changed yet until you reply `YES`.
