# Email Automation Scripts

This directory contains scripts for automating various email communications for the Roundz.ai platform.

## Setup

1. **Prerequisites**:
   - Python 3.x
   - Dependencies from `requirements.txt` installed.
   - Database configuration in `util/config.json` (or `config.json` in the root).

---

## 1. Pending Interview Reminder (`send_pending_interview_reminder.py`)

Sends reminder emails to users who have candidate interviews in a 'PENDING' state that were created more than 3 days ago.

### Usage

**Run Normally** (Send to all eligible users):
```bash
python3 email_automation/send_pending_interview_reminder.py
```

**Test Mode** (Send single email to specific address):
```bash
python3 email_automation/send_pending_interview_reminder.py --test-email your_email@example.com
```

### Logic
- **Filter**: `CandidateInterview.status = 'PENDING'` AND `CandidateInterview.createdAt < NOW() - 3 days`
- **Template**: `interview_data_update/email_templates/pending_interview_reminder.html`

---

## 2. Weekly Digest (`send_weekly_digest.py`)

Generates and sends a weekly digest email containing top community stories, latest blogs, and interview experiences for a specific week.

### Usage

**Preview Mode** (Upload to S3 only):
Generates the HTML for the specified week and uploads a preview to S3 (`s3://navneet-bucket-test/weekly-digest/{year}/week_{week}.html`).

```bash
python3 email_automation/send_weekly_digest.py --week <WEEK_NUMBER> --year <YEAR>
```
*Example:*
```bash
python3 email_automation/send_weekly_digest.py --week 1 --year 2026
```

**Send Mode** (Email all users):
Generates the digest and sends it to all users with validated emails.

```bash
python3 email_automation/send_weekly_digest.py --week <WEEK_NUMBER> --year <YEAR> --send
```

### Logic
- **Data Selection**:
    - **Top Stories**: Top 3 `GroupPost` records created in the ISO week, ordered by `(upvotes + views) DESC`.
    - **Blogs**: Top 3 `Blog` records created in the week, ordered by date.
    - **Interviews**: Top 2 `Interview` records created in the week, ordered by date.
- **Template**: `email_automation/templates/weekly_digest.html` (Jinja2 format).
- **Users**: Sends to all users where `emailValidated = true`.
