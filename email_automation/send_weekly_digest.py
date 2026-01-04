import sys
import os
import argparse
import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Dict, Any

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))

from util.db_helper import DBHelper
from util.aws_helper import AWSHelper
from util.email_helper import EmailHelper
from jinja2 import Template

# Constants
S3_BUCKET = "navneet-bucket-test"

def get_week_dates(year: int, week: int):
    """Calculate start and end dates for a given ISO week."""
    first_day_of_year = datetime.date(year, 1, 4)  # 4th Jan is always in first ISO week
    first_monday = first_day_of_year - datetime.timedelta(days=first_day_of_year.weekday())
    week_start = first_monday + datetime.timedelta(weeks=week - 1)
    week_end = week_start + datetime.timedelta(days=6)
    return week_start, week_end

def fetch_data(db_helper: DBHelper, start_date: datetime.date, end_date: datetime.date):
    """Fetch data for the digest from the database."""
    
    # Format dates for SQL
    start_str = start_date.strftime('%Y-%m-%d 00:00:00')
    end_str = end_date.strftime('%Y-%m-%d 23:59:59')
    
    print(f"Fetching data from {start_str} to {end_str}...")

    # 1. Top Community Stories (GroupPost)
    # Selection criteria: Created in week, ordered by (upvotes + views) DESC, limit 3
    # Need to join User and CommunityGroup
    
    stories_query = f"""
    SELECT 
        gp.id, gp.content, gp."createdAt", gp.upvotes, gp."views", gp."mediaLinkUrl", gp."thumbnailUrl",
        up.name as name,
        cg.name as group_name
    FROM "GroupPost" gp
    JOIN "User" u ON gp."userId" = u.id
    LEFT JOIN "UserProfile" up ON u.id = up."userId"
    JOIN "CommunityGroup" cg ON gp."groupId" = cg.id
    WHERE gp."createdAt" >= '{start_str}' AND gp."createdAt" <= '{end_str}'
    ORDER BY (gp.upvotes + gp."views") DESC
    LIMIT 3
    """
    
    stories_data = db_helper.execute_query(stories_query)
    stories = []
    for row in stories_data:
        # Process content to mimic title/excerpt
        content = row.get('content', '') or ''
        title = (content[:50] + '...') if len(content) > 50 else content
        excerpt = (content[:150] + '...') if len(content) > 150 else content
        
        stories.append({
            'title': title, # synthesizing title
            'url': f"https://roundz.ai/community/post/{row['id']}", # Hypothetical URL
            'author': row.get('name') or 'Anonymous',
            'groupName': row['group_name'],
            'engagementCount': (row['upvotes'] or 0) + (row['views'] or 0),
            'excerpt': excerpt,
            'imageUrl': row['thumbnailUrl'] or row['mediaLinkUrl']
        })

    # 2. Latest Blogs
    # Created in week, limit 3
    blogs_query = f"""
    SELECT 
        id, title, excerpt, slug, author, "date", image, tags, "readTime"
    FROM "Blog"
    WHERE "createdAt" >= '{start_str}' AND "createdAt" <= '{end_str}'
      AND published = true
    ORDER BY "createdAt" DESC
    LIMIT 3
    """
    blogs_data = db_helper.execute_query(blogs_query)
    blogs = []
    for row in blogs_data:
        blogs.append({
            'title': row['title'],
            'url': f"https://roundz.ai/blog/{row['slug']}",
            'excerpt': row['excerpt'],
            'imageUrl': row['image'],
            'category': row['tags'][0] if row['tags'] and len(row['tags']) > 0 else 'General', 
            'author': row['author'],
            'publishedDate': row['date'].strftime('%b %d, %Y') if row['date'] else ''
        })

    # 3. Real Interview Experiences
    # Created in week, limit 2
    interviews_query = f"""
    SELECT 
        i.id, i.title, i."overallRating", i.slug, i.difficulty, i."noOfRounds", i."keyTakeaways",
        i.location, i."interviewProcess",
        c.name as company_name, c."logoUrl" as company_logo
    FROM "Interview" i
    JOIN "Company" c ON i."companyId" = c.id
    WHERE i."date" >= '{start_str}' AND i."date" <= '{end_str}'
    ORDER BY i."date" DESC
    LIMIT 2
    """
    
    interviews_data = db_helper.execute_query(interviews_query)
    interviews = []
    for row in interviews_data:
        # Synthesize experience text from key takeaways or process
        experience_text = row.get('keyTakeaways') or row.get('interviewProcess') or 'Check out this interview experience.'
        excerpt = (experience_text[:120] + '...') if len(experience_text) > 120 else experience_text
        
        interviews.append({
            'companyName': row['company_name'],
            'companyLogo': row['company_logo'],
            'companyInitial': row['company_name'][0] if row['company_name'] else '?',
            'position': row['title'], # Using title as position
            'status': 'Verified', # Placeholder, maybe check status column
            'experience': row.get('overallRating', 'N/A'), # Using rating as experience metric? Template says 'Experience' label.
            # Template has: Experience: {{experience}}, Location: {{location}}, Rounds: {{rounds}}, Difficulty: {{difficulty}}
            # Let's map appropriately.
            'experience': f"{row['overallRating']}/5" if row['overallRating'] else "N/A",
            'location': row['location'] or 'Remote',
            'rounds': row['noOfRounds'],
            'difficulty': row['difficulty'],
            'excerpt': excerpt,
            'url': f"https://roundz.ai/interview/{row['slug']}"
        })

    return {
        'topStories': stories,
        'blogs': blogs,
        'interviews': interviews
    }

def main():
    parser = argparse.ArgumentParser(description='Generate and send Weekly Digest email')
    parser.add_argument('--week', type=int, required=True, help='ISO Week number')
    parser.add_argument('--year', type=int, default=datetime.datetime.now().year, help='Year (default: current year)')
    parser.add_argument('--send', action='store_true', help='Actually send emails to users')
    args = parser.parse_args()

    # 1. Date Range
    try:
        start_date, end_date = get_week_dates(args.year, args.week)
    except Exception as e:
        print(f"Error calculating dates: {e}")
        return

    week_range_str = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
    print(f"Processing for Week {args.week} ({week_range_str})...")

    # 2. Helpers
    db_helper = DBHelper()
    db_helper.connect()
    aws_helper = AWSHelper()
    email_helper = EmailHelper()

    try:
        # 3. Fetch Data
        data = fetch_data(db_helper, start_date, end_date)
        
        if not data['topStories'] and not data['blogs'] and not data['interviews']:
            print("No data found for this week. Exiting.")
            return

        # 4. Render Template
        template_path = Path(__file__).parent / "templates" / "weekly_digest.html"
        with open(template_path, 'r', encoding='utf-8') as f:
            template_str = f.read()

        template = Template(template_str)
        rendered_html = template.render(
            weekRange=week_range_str,
            currentYear=datetime.datetime.now().year,
            userName="{{userName}}", # Keep placeholder for personalized sending, or render assuming preview is generic
            # If for S3 preview, we might want a generic name. If for sending, we need to handle per-user.
            # However, the template expects {{userName}} inside. 
            # Logic: Render the main body content once, but for the personalized greeting, 
            # we might need to do a secondary replace or keep it generic for the preview.
            # For the S3 preview, I will use "Community Member".
            # For the actual send, I will re-render or replace.
            **data
        )
        
        # Render for Preview (fixed name)
        preview_html = template.render(
            weekRange=week_range_str,
            currentYear=datetime.datetime.now().year,
            userName="Community Member",
            **data
        )

        # 5. Upload to S3
        s3_key = f"weekly-digest/{args.year}/week_{args.week}.html"
        print(f"Uploading preview to s3://{S3_BUCKET}/{s3_key}...")
        
        with NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp_file:
            tmp_file.write(preview_html)
            tmp_path = tmp_file.name
        
        try:
            success = aws_helper.upload_file(tmp_path, S3_BUCKET, s3_key, content_type="text/html")
            if success:
                # Assuming public bucket or accessible via console. 
                # If bucket is not public, might need a presigned URL, but req says just upload.
                print(f"Upload successful. Path: s3://{S3_BUCKET}/{s3_key}")
            else:
                print("Upload failed.")
        finally:
            os.remove(tmp_path)

        # 6. Send Emails (if requested)
        if args.send:
            print("Fetching users for email distribution...")
            users_query = """
                SELECT u.id, u.email, up.name 
                FROM "User" u
                LEFT JOIN "UserProfile" up ON u.id = up."userId"
                WHERE u."emailValidated" = true
            """
            users = db_helper.execute_query(users_query) 
            print(f"Found {len(users)} users.")
            
            sent_count = 0
            for user in users:
                user_name = user['name'] or "Community Member"
                user_email = user['email']
                
                # Personalized Render
                user_html = template.render(
                    weekRange=week_range_str,
                    currentYear=datetime.datetime.now().year,
                    userName=user_name,
                    **data
                )
                
                subject = f"Your Weekly Digest: Week {args.week}"
                
                # Send
                try:
                    email_helper.send_email(subject, user_html, user_email, is_html=True)
                    sent_count += 1
                    if sent_count % 10 == 0:
                        print(f"Sent {sent_count} emails...")
                except Exception as e:
                    print(f"Failed to send to {user_email}: {e}")
            
            print(f"Finished sending. Total sent: {sent_count}")
        else:
            print("\nPreview uploaded. Run with --send to email all users.")

    finally:
        db_helper.close()

if __name__ == "__main__":
    main()
