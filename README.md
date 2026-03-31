# Scheduler-AI - Intelligent Meeting Scheduler

Scheduler-AI is a backend-first scheduling system that finds high-quality meeting slots across multiple participants using calendar availability, risk-aware ranking, and automated reminder flows.

## What It Does

- Connects user calendars (Google and Microsoft OAuth flows)
- Fetches busy events and computes participant free slots
- Intersects availability across attendees for a required duration
- Ranks candidate slots by risk and feasibility
- Handles RSVP responses and declined-meeting workflows
- Sends invite/reminder notifications with ICS attachments

## Tech Stack

- Python
- FastAPI
- APScheduler
- OAuth (Google / Microsoft)
- SQLAlchemy models and Alembic migrations

## Core Features

### 1) Smart Slot Discovery
- Working-hours filtering per user
- Availability intersection for multi-attendee meetings
- Top candidate slot selection

### 2) Risk-Aware Ranking
- Proximity-to-window-end scoring
- Buffer penalties between adjacent meetings (15-minute buffer logic)
- Feasibility score output per recommendation

### 3) Scheduling Workflow
- Propose meeting slots
- Confirm chosen slot
- RSVP accept/decline handling
- Alternative suggestions when participants reject

### 4) Communication Automation
- ICS invite generation
- Notification dispatch endpoints
- Priority-based periodic reminders via APScheduler

## Project Structure

```text
app/
  server.py                     # FastAPI app + route registration
  db/
    models.py                   # Users, meetings, participants, declines, events
  v1/
    schedule/                   # Find/confirm slot APIs
    oauth/                      # Google/Microsoft OAuth routes/services
    communication/              # Notification trigger APIs
    notifications/              # Periodic reminder scheduler
    rsvp/                       # Accept/decline endpoints
    alternative_suggestions/    # Post-rejection rescheduling
core/
  scheduler.py                  # Availability filtering + risk ranking engine
  google/calendar.py            # Google Calendar integrations
  microsoft/calendar.py         # Microsoft calendar integrations
start.py                        # Uvicorn launcher
config.py                       # Environment-driven settings
```

## Quick Start

### 1) Clone and install

```bash
git clone <your-repo-url>
cd meetingassisst-main
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If your local repo does not include `requirements.txt`, install dependencies from your environment lock/source and then generate one for consistency.

### 2) Configure environment

Create `.env` from `.env.sample` and fill values:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `MICROSOFT_CLIENT_ID`
- `MICROSOFT_CLIENT_SECRET`
- `MICROSOFT_REDIRECT_URI`
- `SECRET_KEY`
- Email settings (SMTP host/user/password/from)

### 3) Run the app

```bash
python start.py
```

Server runs on:

- `http://0.0.0.0:8000`

## High-Level API Surface

- `/v1/oauth/*` - OAuth auth/callback flows
- `/v1/scheduler/*` - find and confirm meeting slots
- `/api/v1/rsvp/*` - invitation response handling
- `/api/v1/communication/*` - notification trigger routes
- `/api/v1/notifications/*` - periodic reminder workflows

## Resume-Ready Highlights

- Built a FastAPI-based scheduling system that computes and ranks meeting slots across participants.
- Implemented risk/feasibility scoring using deadline proximity and buffer-aware heuristics.
- Delivered RSVP + reminder automation with OAuth calendar integrations and ICS invite workflows.

## Security Notes

- Never hardcode API keys or tokens in source files.
- Store secrets in `.env` and keep `.env` out of version control.
- Rotate exposed credentials immediately if committed accidentally.

