# Pending Interview Reminder Script

This script sends reminder emails to users who have candidate interviews in a 'PENDING' state that were created more than 3 days ago.

## Setup

1. **Prerequisites**:
   - Python 3.x
   - Dependencies from `requirements.txt` installed.
   - Database configuration in `util/config.json` (or `config.json` in the root).

## Usage

### Run Normally
To send reminders to all eligible users:

```bash
python3 email_automation/send_pending_interview_reminder.py
```

### Test Mode
To send a single test email to a specific address without processing the full list:

```bash
python3 email_automation/send_pending_interview_reminder.py --test-email your_email@example.com
```

## Logic

1.  **Filter**: Selects users with:
    -   `CandidateInterview.status = 'PENDING'`
    -   `CandidateInterview.createdAt < NOW() - 3 days`
2.  **Email**:
    -   Uses the template at `interview_data_update/email_templates/pending_interview_reminder.html`.
    -   Replaces `{{action_url}}` with `http://roundz.ai/my-interview`.
