import sys
import sqlite3
from pathlib import Path
import datetime
import argparse

# Add parent directory to sys.path to allow importing util
sys.path.append(str(Path(__file__).parent.parent))

from util.db_helper import DBHelper
from util.email_helper import EmailHelper

# Configuration
LOCAL_DB_NAME = "welcome_sent_log.db"
SUBJECT = "before you start, one quick thing"

WELCOME_EMAIL_BODY = """Hi {name},

Really glad you joined Roundz AI.

We built Roundz AI to help candidates learn from real interview experiences, understand how hiring is changing, and practice in a way that actually feels close to the real thing.

If you don’t mind, I’d love to ask one quick question.
What made you sign up for Roundz AI?

Your answer helps us understand what you’re hoping to improve, whether that’s confidence, preparation, or clarity about how hiring works today. Just hit reply and share a line or two.

Over the next couple of weeks, we’ll send a few short emails to help you get value from the platform. We’ll share interview insights, common patterns we’re seeing across companies, and simple ways to practice more effectively.

Glad you’re here, and excited to be part of your preparation journey.

Best,
Navneet
Founder, Roundz AI"""

def setup_local_db():
    """Setup SQLite database to track sent emails."""
    db_path = Path(__file__).parent / LOCAL_DB_NAME
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sent_emails (
            user_id TEXT PRIMARY KEY,
            email TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def is_already_sent(conn, user_id):
    """Check if email was already sent to this user."""
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM sent_emails WHERE user_id = ?', (user_id,))
    return cursor.fetchone() is not None

def log_sent_email(conn, user_id, email):
    """Record that email was sent to this user."""
    cursor = conn.cursor()
    cursor.execute('INSERT INTO sent_emails (user_id, email) VALUES (?, ?)', (user_id, email))
    conn.commit()

def main():
    parser = argparse.ArgumentParser(description='Send welcome emails to new users')
    parser.add_argument('--test-email', help='Send a single test email to this address and exit')
    parser.add_argument('--dry-run', action='store_true', help='Print actions without sending emails')
    args = parser.parse_args()

    print("Starting Welcome Email Script...")

    # 1. Initialize Helpers and Local DB
    try:
        db_helper = DBHelper()
        db_helper.connect()
        print("✓ PostgreSQL connected")
        
        email_helper = EmailHelper()
        print("✓ Email helper initialized")
        
        local_conn = setup_local_db()
        print(f"✓ Local tracking DB ({LOCAL_DB_NAME}) initialized")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return

    # 2. Handle Test Mode
    if args.test_email:
        print(f"\n--- TEST MODE ---")
        print(f"Sending single test email to: {args.test_email}")
        body = WELCOME_EMAIL_BODY.format(name="there")
        if email_helper.send_email(SUBJECT, body, args.test_email, is_html=False):
            print(f"✓ Test email sent successfully to {args.test_email}")
        else:
            print(f"✗ Failed to send test email")
        
        db_helper.close()
        local_conn.close()
        return

    # 3. Query Recently Joined Users
    # Users joined in the last 24 hours
    query = """
    SELECT u.id, u.email, up.name
    FROM "User" u
    LEFT JOIN "UserProfile" up ON u.id = up."userId"
    WHERE u."createdAt" >= NOW() - INTERVAL '1 day'
    """
    
    try:
        new_users = db_helper.execute_query(query)
        print(f"✓ Found {len(new_users)} users who joined in the last 24 hours")
    except Exception as e:
        print(f"✗ Failed to fetch users from PostgreSQL: {e}")
        db_helper.close()
        local_conn.close()
        return

    # 4. Process and Send Emails
    sent_count = 0
    skipped_count = 0
    fail_count = 0

    print("\nProcessing users...")
    for user in new_users:
        user_id = user['id']
        email = user['email']
        name = user.get('name') or "there"

        # Check deduplication
        if is_already_sent(local_conn, user_id):
            print(f"  - Skipping {email} (Already sent)")
            skipped_count += 1
            continue

        body = WELCOME_EMAIL_BODY.format(name=name)

        if args.dry_run:
            print(f"  [DRY-RUN] Would send to {email} ({name})")
            sent_count += 1
            continue

        print(f"  → Sending to {email} ({name})...", end="", flush=True)
        if email_helper.send_email(SUBJECT, body, email, is_html=False):
            print(" ✓ Sent")
            log_sent_email(local_conn, user_id, email)
            sent_count += 1
        else:
            print(" ✗ Failed")
            fail_count += 1

    print("\n=== Summary ===")
    print(f"Total New Users: {len(new_users)}")
    print(f"Emails Sent: {sent_count}")
    print(f"Skipped (Duplicates): {skipped_count}")
    print(f"Failed: {fail_count}")

    db_helper.close()
    local_conn.close()

if __name__ == "__main__":
    main()
