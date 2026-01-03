import sys
from pathlib import Path
import os
from typing import List

# Add parent directory to sys.path to allow importing util
sys.path.append(str(Path(__file__).parent.parent))

from util.db_helper import DBHelper
from util.email_helper import EmailHelper

def main():
    print("Starting Pending Interview Reminder Script...")

    # 1. Initialize Helpers
    try:
        db_helper = DBHelper()
        db_helper.connect()
        print("✓ Database connected")
        
        email_helper = EmailHelper()
        print("✓ Email helper initialized")
    except Exception as e:
        print(f"✗ Failed to initialize helpers: {e}")
        return

    # 2. Query Users with PENDING interviews
    # Using generic 'PENDING' status as per schema
    # Distinct emails to avoid spamming multiple emails for multiple pending interviews
    query = """
    SELECT DISTINCT u.email 
    FROM "User" u
    JOIN "CandidateInterview" ci ON u.id = ci."userId"
    WHERE ci.status = 'PENDING'
      AND ci."createdAt" < NOW() - INTERVAL '3 days'
    """
    
    try:
        users = db_helper.execute_query(query)
        print(f"✓ Found {len(users)} users with pending interviews")
    except Exception as e:
        print(f"✗ Failed to fetch users: {e}")
        return

    if not users:
        print("No pending interviews found. Exiting.")
        return

    # 3. Read Email Template
    template_path = Path(__file__).parent.parent / "interview_data_update" / "email_templates" / "pending_interview_reminder.html"
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        print("✓ Template loaded")
    except Exception as e:
        print(f"✗ Failed to load template from {template_path}: {e}")
        return

    # 4. Send Emails
    action_url = "http://roundz.ai/my-interview"
    subject = "Reminder: Complete Your Interview on Roundz AI"
    
    success_count = 0
    fail_count = 0

    print("\nSending emails...")
    for user in users:
        email = user.get('email')
        if not email:
            print("  ⚠ Skipping user with no email")
            continue

        # Simple template substitution
        # Since we don't have user names in the query (schema didn't explicitly show a name column in User table, checking again...)
        # User table columns: id, email, password, provider, providerAccountId, role, avatarUrl... No name/username.
        # So generic greeting is appropriate.
        
        email_body = template_content.replace("{{action_url}}", action_url)
        
        print(f"  → Sending to {email}...")
        
        # In a real dry-run scenario we might want a flag, but for now we will send as per requirement.
        # Ensure 'SafeToAutoRun' in tool call? The user asked to implement logic.
        
        if email_helper.send_email(subject, email_body, email, is_html=True):
            print(f"    ✓ Sent")
            success_count += 1
        else:
            print(f"    ✗ Failed")
            fail_count += 1

    print("\n=== Summary ===")
    print(f"Total Users: {len(users)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")

    db_helper.close()

if __name__ == "__main__":
    main()
