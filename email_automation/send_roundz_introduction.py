import sys
import os
import csv
import argparse
import markdown
from pathlib import Path
from typing import Optional

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))

from util.email_helper import EmailHelper

EMAIL_BODY_TEMPLATE = """Hi {name},

We know how stressful final year can feel.

Preparing for internships while managing classes, projects, and constant uncertainty is not easy. Many students tell us the hardest part isn’t studying, it’s **not knowing what interviewers actually expect**, what to focus on, and whether they’re preparing the *right way*.

That’s exactly why we built **Roundz**.

Roundz is an **AI-based interview practice platform** designed to help students like you practice interviews in a realistic way. We standardize interview experiences for different roles and levels so you get clarity on:

* What interview questions really look like
* What topics matter most — and what you can safely skip
* How to feel confident walking into an interview

Along with this, we’ve started a **Discord community** where students preparing for internships come together to:

* Share preparation strategies and resources
* Discuss interview experiences
* Support each other during the process

You don’t have to prepare alone.

👉 **Explore Roundz:** https://roundz.ai/

👉 **Join our Discord community:** https://discord.com/invite/pr4dPAeVhU

If this helps even a little in making your preparation clearer or less stressful, we’ll consider it worth it.

Wishing you confidence and success ahead,

-- Naveen
"""

def format_name(name: str) -> str:
    """
    Formats the name to be PascalCase with spaces.
    Example: "navneet rabadiya" -> "Navneet Rabadiya"
    """
    if not name:
        return "Student" # Fallback
    return name.strip().title()

def main():
    parser = argparse.ArgumentParser(description='Send Roundz introduction emails to candidates from a CSV file.')
    parser.add_argument('--csv', default='candidates.csv', help='Path to the CSV file containing candidates (default: candidates.csv)')
    parser.add_argument('--test-email', help='If provided, all emails will be sent to this address instead of the candidate\'s actual email.')
    parser.add_argument('--send', action='store_true', help='Actually send the emails. If not set, performs a dry run.')
    
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        # Try looking in the same directory as the script if strictly filename provided
        script_dir = Path(__file__).parent
        csv_path = script_dir / args.csv
        
        if not csv_path.exists():
            print(f"Error: CSV file not found at {args.csv}")
            return

    email_helper = EmailHelper()
    
    print(f"Reading candidates from {csv_path}...")
    
    candidates = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'Name' in row and 'Email' in row:
                    candidates.append(row)
                else:
                    print(f"Warning: Skipping row with missing Name or Email header: {row}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    print(f"Found {len(candidates)} candidates.")
    
    sent_count = 0
    
    for candidate in candidates:
        original_name = candidate['Name']
        email = candidate['Email']
        
        formatted_name = format_name(original_name)
        
        # Format the markdown body with the name
        markdown_body = EMAIL_BODY_TEMPLATE.format(name=formatted_name)
        
        # Convert Markdown to HTML
        html_body = markdown.markdown(markdown_body)
        
        # Wrap in a basic nice-to-have HTML structure if native markdown is too raw,
        # but markdown library output is just the tags <p>, <ul> etc.
        # Let's wrap it in a div with some basic font styling to look professional.
        final_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto;">
                {html_body}
            </div>
        </body>
        </html>
        """
        
        subject = "Your Interview Prep Journey" 

        recipient_email = args.test_email if args.test_email else email
        
        if args.send:
            print(f"Sending HTML email to {formatted_name} <{recipient_email}>...")
            try:
                success = email_helper.send_email(subject, final_html, recipient_email, is_html=True)
                if success:
                    sent_count += 1
                else:
                    print(f"Failed to send email to {recipient_email}")
            except Exception as e:
                print(f"Exception sending to {recipient_email}: {e}")
        else:
            print(f"[DRY RUN] Would send HTML email to: {formatted_name} <{recipient_email}>")
            # print(f"--- HTML Body Preview for {formatted_name} ---\n{final_html}\n-----------------------------------")

    if args.send:
        print(f"\nFinished. Sent {sent_count} emails.")
    else:
        print("\nDry run completed. Use --send to actually send emails.")

if __name__ == "__main__":
    main()
