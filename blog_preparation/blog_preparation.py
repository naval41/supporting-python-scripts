import boto3
import json
import os
import re
import shutil
from pathlib import Path
from typing import Dict, Any
import html
import sys
# Add parent directory to sys.path to allow importing util
sys.path.append(str(Path(__file__).parent.parent))

from util.aws_helper import AWSHelper
from util.config import Config
from twitter_post import call_bedrock_for_twitter_thread

# Load environment variables from .env file if it exists
def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Only set if not already set in environment
                    if key.strip() not in os.environ:
                        os.environ[key.strip()] = value.strip()

# Load .env file at module import
load_env_file()


# Local config loading and client creation functions removed - replaced by util package


def call_bedrock_for_metadata(bedrock_client, markdown_content: str, model_id: str) -> Dict[str, Any]:
    """
    Call Bedrock API to extract metadata from blog content.
    
    Args:
        bedrock_client: boto3 bedrock client
        markdown_content: Content of the blog
        model_id: Bedrock model ID
        
    Returns:
        Dictionary containing metadata
    """
    try:
        bedrock = bedrock_client
        
        prompt = """Extract the following information from this blog post and return ONLY a JSON object with these exact keys:
{
  "title": "Title of the blog",
  "slug": "url-friendly-slug",
  "time_to_read": "X min read",
  "tags": "tag1, tag2, tag3",
  "excerpt": "A concise summary of the article in 300 characters. It should be SEO and AEO and Agent friendly.",
}

Rules:
- Title: Extract or infer the main title
- Excerpt: A concise summary of the article in 300 characters. It should be SEO and AEO and Agent friendly.
- Slug: Create a URL-friendly version of the title (lowercase, hyphens instead of spaces, no special chars)
- Time to read: Estimate reading time (assume 200 words per minute)
- Tags: Extract 3-5 relevant tags, comma-separated
- Return ONLY the JSON, no other text"""

        message = {
            "role": "user",
            "content": [
                {"text": f"<content>{markdown_content}</content>"},
                {"text": prompt}
            ]
        }
        
        print("Calling Bedrock for metadata extraction...")
        
        response = bedrock.converse(
            modelId=model_id,
            messages=[message],
            inferenceConfig={
                "maxTokens": 1000,
                "temperature": 0
            }
        )
        
        response_text = response['output']['message']['content'][0]['text']
        
        # Extract JSON from response
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            metadata = json.loads(json_match.group())
            return metadata
        else:
            print(f"Warning: Could not extract JSON from response: {response_text}")
            return {}
            
    except Exception as e:
        print(f"Error calling Bedrock API: {e}")
        return {}


def upload_images_to_s3(s3_client, slug: str, images_dir: Path, bucket_name: str, s3_folder_path: str):
    """
    Create S3 folder and upload all images from images directory.
    
    Args:
        s3_client: boto3 S3 client
        slug: Blog slug for folder name
        images_dir: Local directory containing images
        bucket_name: S3 bucket name
        s3_folder_path: Base folder path in S3
    """
    try:
        s3 = s3_client
        
        # Construct the S3 folder path
        s3_prefix = f"{s3_folder_path}/{slug}/"
        
        print(f"Uploading images to s3://{bucket_name}/{s3_prefix}")
        
        # Content-Type mapping for different image extensions
        content_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml'
        }
        
        # List all image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        image_files = [
            f for f in images_dir.iterdir() 
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
        
        for image_file in image_files:
            s3_key = f"{s3_prefix}{image_file.name}"
            file_extension = image_file.suffix.lower()
            content_type = content_type_map.get(file_extension, 'application/octet-stream')
            
            print(f"Uploading {image_file.name} (Content-Type: {content_type}) to s3://{bucket_name}/{s3_key}")
            
            # Upload with Content-Type metadata
            s3.upload_file(
                str(image_file), 
                bucket_name, 
                s3_key,
                ExtraArgs={'ContentType': content_type}
            )
            print(f"Successfully uploaded {image_file.name}")
            
    except Exception as e:
        print(f"Error uploading images to S3: {e}")


def copy_images_to_output(images_dir: Path, output_dir: Path):
    """
    Copy all images from input/images directory to output directory.
    
    Args:
        images_dir: Local directory containing images (input/images)
        output_dir: Output directory where images should be copied (output/slug)
    """
    try:
        if not images_dir.exists() or not images_dir.is_dir():
            print(f"Warning: Images directory not found at {images_dir}")
            return
        
        # Create Images folder in output directory
        output_images_dir = output_dir / "Images"
        output_images_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Copying images to {output_images_dir}")
        
        # List all image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        image_files = [
            f for f in images_dir.iterdir() 
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
        
        if not image_files:
            print(f"Warning: No image files found in {images_dir}")
            return
        
        # Copy each image file
        for image_file in image_files:
            dest_file = output_images_dir / image_file.name
            shutil.copy2(image_file, dest_file)
            print(f"Copied {image_file.name} to {dest_file}")
        
        print(f"Successfully copied {len(image_files)} image(s) to {output_images_dir}")
        
    except Exception as e:
        print(f"Error copying images to output directory: {e}")


def _to_unicode_styled(text: str, style: str) -> str:
    """
    Convert ASCII letters/digits in text to Unicode styled variants.
    Supported styles: 'bold', 'italic'.
    Uses Sans-Serif Bold/Italic to maintain same font family as regular text.
    """
    # Maps for Latin letters (A-Z, a-z) and digits 0-9 to Sans-Serif styled symbols
    # Sans-Serif Bold letters (same font family, just bold)
    bold_upper = {chr(ord('A') + i): chr(0x1D5D4 + i) for i in range(26)}
    bold_lower = {chr(ord('a') + i): chr(0x1D5EE + i) for i in range(26)}
    bold_digits = {chr(ord('0') + i): chr(0x1D7E2 + i) for i in range(10)}
    # Sans-Serif Italic letters (same font family, just italic)
    italic_upper = {chr(ord('A') + i): chr(0x1D608 + i) for i in range(26)}
    italic_lower = {chr(ord('a') + i): chr(0x1D622 + i) for i in range(26)}

    result_chars = []
    for ch in text:
        if style == 'bold':
            if ch in bold_upper:
                result_chars.append(bold_upper[ch])
            elif ch in bold_lower:
                result_chars.append(bold_lower[ch])
            elif ch in bold_digits:
                result_chars.append(bold_digits[ch])
            else:
                result_chars.append(ch)
        elif style == 'italic':
            if ch in italic_upper:
                result_chars.append(italic_upper[ch])
            elif ch in italic_lower:
                result_chars.append(italic_lower[ch])
            else:
                result_chars.append(ch)
        else:
            result_chars.append(ch)
    return ''.join(result_chars)


def format_linkedin_content(markdown_content: str, style: str = None) -> str:
    """
    Format markdown-ish content for LinkedIn according to style.
    style options:
    - 'plain': strip markdown markers, do NOT use unicode styling (accessible, searchable)
    - 'markdown': keep markers as-is (no transformation)
    - 'unicode': convert **bold**/*italic* to Unicode styled characters (visual emphasis, not searchable)
    The default can be configured via env var LINKEDIN_FORMAT_STYLE, default 'unicode'.
    """
    # Check environment variable at runtime, not at module import
    selected_style = style or os.getenv('LINKEDIN_FORMAT_STYLE', 'unicode').lower()
    content = markdown_content

    # Normalize CRLF
    content = content.replace('\r\n', '\n')

    # Remove unsupported features regardless of style (headers, links, code, blockquotes, hr)
    content = re.sub(r'^#{1,6}\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'\s#{1,6}\s*', ' ', content)
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
    content = re.sub(r'^- ', '• ', content, flags=re.MULTILINE)
    content = re.sub(r'```[^`]*```', '', content, flags=re.DOTALL)
    content = re.sub(r'`([^`]+)`', r'\1', content)
    content = re.sub(r'^>\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'^---+$', '', content, flags=re.MULTILINE)

    if selected_style == 'markdown':
        # Leave markers as-is
        pass
    elif selected_style == 'plain':
        # Strip bold/italic markers but keep text
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
        content = re.sub(r'__(.*?)__', r'\1', content)
        content = re.sub(r'\*(.*?)\*', r'\1', content)
        content = re.sub(r'_(.*?)_', r'\1', content)
    elif selected_style == 'unicode':
        # Convert bold then italic using non-greedy groups
        def bold_repl(m):
            return _to_unicode_styled(m.group(1), 'bold')
        def italic_repl(m):
            return _to_unicode_styled(m.group(1), 'italic')
        # Handle __bold__ and **bold**
        content = re.sub(r'\*\*(.*?)\*\*', lambda m: bold_repl(m), content, flags=re.DOTALL)
        content = re.sub(r'__(.*?)__', lambda m: bold_repl(m), content, flags=re.DOTALL)
        # Handle *italic* and _italic_
        # Avoid converting inside already-converted bold unicode; order helps reduce overlap
        content = re.sub(r'(?<!\*)\*(?!\*)(.*?)\*(?<!\*)', lambda m: italic_repl(m), content, flags=re.DOTALL)
        content = re.sub(r'_(.*?)_', lambda m: italic_repl(m), content, flags=re.DOTALL)
        # Remove remaining markers (if any leftover mismatches)
        content = re.sub(r'\*\*|__|\*|_', '', content)
    else:
        # Fallback to plain
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
        content = re.sub(r'__(.*?)__', r'\1', content)
        content = re.sub(r'\*(.*?)\*', r'\1', content)
        content = re.sub(r'_(.*?)_', r'\1', content)

    # Clean up multiple newlines
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    return content.strip()


def update_markdown_images(markdown_content: str, slug: str, images_dir: Path, cdn_base_url: str) -> str:
    """
    Update image references in markdown to use CDN URLs.
    
    Args:
        markdown_content: Original markdown content
        slug: Blog slug
        images_dir: Directory containing images
        cdn_base_url: Base CDN URL
        
    Returns:
        Updated markdown content
    """
    # Find all markdown image references: ![](path) or ![alt](path)
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    def replace_image(match):
        alt_text = match.group(1)
        image_path = match.group(2)
        
        # Extract just the filename
        image_name = os.path.basename(image_path)
        
        # Construct CDN URL
        cdn_url = f"{cdn_base_url}{slug}/{image_name}"
        
        return f'![{alt_text}]({cdn_url})'
    
    updated_content = re.sub(pattern, replace_image, markdown_content)
    return updated_content


def call_bedrock_for_linkedin_post(bedrock_client, markdown_content: str, metadata: Dict[str, Any], model_id: str) -> str:
    """
    Call Bedrock API to generate LinkedIn post content.
    
    Args:
        bedrock_client: boto3 bedrock client
        markdown_content: Blog content
        metadata: Blog metadata
        model_id: Bedrock model ID
        
    Returns:
        LinkedIn post content
    """
    try:
        bedrock = bedrock_client
        
        prompt = """Please produce one LinkedIn post only based on the blog content provided below. Follow these constraints exactly:

Tone & structure
• Storytelling first, professional and practical overall. Start with a short anecdote or scene from the blog content, written like a real person telling a story.
• The first two lines must be catchy and hook the reader. Keep them short and punchy.
• Use short, clear sentences. Vary sentence structure. Include natural breaks and a few small imperfections so it sounds human and spontaneous. Do not sound over-polished or robotic.
• Write in a friendly, conversational voice — approachable and authentic, as if posting to LinkedIn or Reddit-style tech communities.
• Avoid em dashes. Use commas, periods, or conjunctions instead.
• No headers, no code blocks, no inline links. Do not include markdown headers.
• Use bold and italic markers for emphasis where helpful.
• Use • bullets and emojis for lists and takeaways (moderate emoji use). Do not overuse emojis.
• One key requirement: include key takeaways presented as emoji bullets. For each takeaway, show a single bullet point title followed by one paragraph of deeper explanation that a fellow engineer can act on. Also include a one-line summary sentence after the detailed explanation for quick scanning.
• Keep the post readable in one LinkedIn post — target ~8–14 short lines including bullets, but prioritize clarity over an exact line count.

Style specifics
• Storyline opener, then quick context, then a short list of actionable takeaways, then a closing CTA.
• Use short statements and avoid repetitive phrasing.
• Use moderate emojis, e.g., one emoji per bullet and 1–2 elsewhere max.
• Emphasize learning and practical advice for engineers.
• End with an inviting call to action: encourage readers to join our Discord community at https://discord.com/invite/4UZr8q48 for discussions, networking, and more insights. Provide the CTA naturally as a sentence. Use a clear, friendly close: invite comments, reactions, or questions.

Formatting rules (must follow)
• Use bold and italic for emphasis.
• Use • bullets and emojis for the takeaways. Example format for each takeaway:
• ✅ Takeaway title — One paragraph explaining what it means, how to apply it, and why it matters for engineers. Then a single summary sentence.
• No raw markdown headers, no code fences, no inline clickable links. If a URL is required, place it plainly as text or use a placeholder like [BLOG_URL].
• Produce a single LinkedIn post only. Do not produce multiple versions.

<sample_linkedin_post_example>

"System design preparation:
You've watched 50 hours of system design videos.
You've memorized every diagram from Grokking.
You've bookmarked 30 articles on microservices

Results:
Still no offer, and you're losing confidence in yourself.

System design interviews aren't harder because companies have raised the bar.
You're just preparing like it's still 2019.

5-6 years ago, you could sketch a load balancer, add a database, call it "microservices" and pass.
Now interviewers expect you to explain workflow engines, geospatial indexing, and real-time data pipelines.

The problem isn't that there's more to learn.
It's that most people are learning it wrong.

Stop memorizing theory
Start solving real problems.

Here's how I learned system design at Google, and how I would practice it now:

Pick a system.
Design it from scratch.
Like you're building it tomorrow.

Try these 10 problems:

URL Shortener: unique IDs, collision handling, billion-scale reads

Dropbox: file sync, versioning, conflict resolution

News Feed: ranking, real-time delivery, personalization at scale

WhatsApp: offline messages, delivery receipts, chat history

Uber: live location tracking, driver matching, payment flows

Instagram Stories: auto-deletion, concurrent views, temporary storage

YouTube: video upload, streaming, recommendations, traffic spikes

Calendly: time zones, double-booking prevention, reminders

E-commerce Checkout: cart sync, inventory management, flash sales

Google Docs: live collaboration, conflict-free editing, version control

After 5-6 problems, you'll notice patterns: caching, queues, rate limiting, and partitioning.

That's when concepts click.

This is exactly why we built Layrs (layrs.me). Interactive canvas, real problems, instant feedback on your designs.

Join our Discord community at https://discord.com/invite/4UZr8q48 for more discussions, networking, and insights from fellow engineers!

No one expects perfection.

They want to see you think through real constraints and explain your choices clearly."

Closing CTA requirement (include one of these options in the post):
• Option A: Invite readers to join our Discord community at https://discord.com/invite/4UZr8q48 for discussions, networking, and more insights from fellow engineers. Phrase it naturally, not salesy.
• Option B: Invite readers to read the full blog at [BLOG_URL] and join our Discord community at https://discord.gg/6DgrhnxD to continue the conversation with other engineers.

Deliverable: Return a single LinkedIn post that follows every instruction above, uses the blog content, and ends with the required CTA that includes the Discord invitation.**
</sample_linkedin_post_example>
"""
        
        message = {
            "role": "user",
            "content": [
                {"text": f"Blog Title: {metadata.get('title', '')}"},
                {"text": f"Blog Content:\n{markdown_content}"},
                {"text": prompt}
            ]
        }
        
        print("Calling Bedrock for LinkedIn post generation...")
        
        response = bedrock.converse(
            modelId=model_id,
            messages=[message],
            inferenceConfig={
                "maxTokens": 2000,
                "temperature": 0.7
            }
        )
        
        # Check if response has the expected structure
        if 'output' not in response:
            print(f"Error: Unexpected response structure - no 'output' key. Response: {response}")
            return ""
        
        if 'message' not in response['output']:
            print(f"Error: Unexpected response structure - no 'message' key. Response: {response}")
            return ""
        
        if 'content' not in response['output']['message']:
            print(f"Error: Unexpected response structure - no 'content' key. Response: {response}")
            return ""
        
        if not response['output']['message']['content']:
            print(f"Error: Empty content in response. Response: {response}")
            return ""
        
        post_content = response['output']['message']['content'][0]['text']
        
        if not post_content or not post_content.strip():
            print(f"Error: Empty post content received from Bedrock API")
            return ""
        
        # Convert markdown formatting to LinkedIn-compatible format using configured style
        post_content = format_linkedin_content(post_content)
        
        print(f"Successfully generated LinkedIn post ({len(post_content)} characters)")
        return post_content
        
    except KeyError as e:
        print(f"Error: Missing key in Bedrock response: {e}")
        try:
            print(f"Response structure: {response}")
        except NameError:
            print("Response was not received before error occurred")
        return ""
    except Exception as e:
        print(f"Error calling Bedrock API for LinkedIn post: {e}")
        import traceback
        traceback.print_exc()
        return ""


def call_bedrock_for_carousel(bedrock_client, markdown_content: str, metadata: Dict[str, Any], model_id: str) -> str:
    """
    Call Bedrock API to generate LinkedIn carousel content (5-8 slides).
    
    Args:
        bedrock_client: boto3 bedrock client
        markdown_content: Blog content
        metadata: Blog metadata
        model_id: Bedrock model ID
        
    Returns:
        Carousel content
    """
    try:
        bedrock = bedrock_client
        
        prompt = """Create a LinkedIn carousel post with 5-8 slides based on this blog content. Each slide should be concise and focused on a single key point.

Guidelines for each slide:
- Keep the title/topic short and punchy (one line)
- Use 2-4 bullet points or a short paragraph for the content
- Add suggestion if slide can be have any image which is present in blog for that section. Add name of the diagram image based on blog.
- Focus on actionable insights, key learnings, or important takeaways
- Use **bold** for emphasis where needed
- Keep each slide's content under 150-200 words

Structure the carousel as follows:
1. Title slide or attention-grabbing opener
2-7. Key points/concepts from the blog, have this detailed and in depth.
8. Call-to-action or summary slide

Format each slide clearly with a "Slide X:" heading followed by the content. The content should be engaging, professional, and suitable for a LinkedIn carousel.

IMPORTANT: Use **bold** and *italic* markers for emphasis. Use • bullets for lists. Do not include markdown headers, code blocks, or inline links. Produce a carousel with 5-8 slides total."""
        
        message = {
            "role": "user",
            "content": [
                {"text": f"Blog Title: {metadata.get('title', '')}"},
                {"text": f"Blog Content:\n{markdown_content}"},
                {"text": prompt}
            ]
        }
        
        print("Calling Bedrock for carousel generation...")
        
        response = bedrock.converse(
            modelId=model_id,
            messages=[message],
            inferenceConfig={
                "maxTokens": 2000,
                "temperature": 0.7
            }
        )
        
        carousel_content = response['output']['message']['content'][0]['text']
        
        # Convert markdown formatting to LinkedIn-compatible format using configured style
        carousel_content = format_linkedin_content(carousel_content)
        
        return carousel_content
        
    except Exception as e:
        print(f"Error calling Bedrock API for carousel: {e}")
        return ""


def main():
    """
    Main function to process blog preparation.
    """
    # Configuration
    model_id = "arn:aws:bedrock:ap-south-1:339713139204:inference-profile/apac.anthropic.claude-sonnet-4-20250514-v1:0"
    bucket_name = "roundz-static-asset-prod"  # Update with your actual bucket name
    s3_folder_path = "static-asset/blog_images"  # Update with your S3 folder path
    cdn_base_url = "https://d5osvdbc8um23.cloudfront.net/static-asset/blog_images/"
    
    # Directory paths
    work_dir = Path(__file__).parent
    input_dir = work_dir / "input"
    output_dir = work_dir / "output"
    config_file = work_dir / "aws_config.json"
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load AWS configuration
    print("Loading AWS configuration...")
    # Use centralized config loading
    aws_config = Config.load_aws_config(str(config_file))
    
    if not aws_config:
        print("Error: Failed to load AWS configuration")
        return
    
    # Create AWS clients
    print("Creating AWS clients...")
    # Use generic AWSHelper
    aws_helper = AWSHelper(aws_config)
    bedrock_client = aws_helper.get_bedrock_client()
    s3_client = aws_helper.get_s3_client()
    
    if not bedrock_client:
        print("Error: Failed to create Bedrock client")
        return
    
    if not s3_client:
        print("Error: Failed to create S3 client")
        return
    
    # Find markdown file in input directory
    markdown_files = list(input_dir.glob("*.md"))
    if not markdown_files:
        print("Error: No markdown files found in input directory")
        return
    
    markdown_file = markdown_files[0]
    print(f"Processing blog: {markdown_file.name}")
    
    # Read markdown file
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Step 1: Extract metadata using Bedrock
    print("\n=== Step 1: Extracting Metadata ===")
    metadata = call_bedrock_for_metadata(bedrock_client, markdown_content, model_id)
    
    if not metadata:
        print("Error: Failed to extract metadata")
        return
    
    slug = metadata.get('slug', 'untitled')
    
    # Create slug-based output directory
    slug_output_dir = output_dir / slug
    slug_output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created output directory: {slug_output_dir}")
    
    # Save metadata to output folder
    metadata_file = slug_output_dir / "metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)
    
    print(f"Metadata saved to {metadata_file}")
    print(f"Extracted metadata: {json.dumps(metadata, indent=2)}")
    
    # Step 2: Upload images to S3
    print("\n=== Step 2: Uploading Images to S3 ===")
    images_dir = input_dir / "images"
    if images_dir.exists() and images_dir.is_dir():
        upload_images_to_s3(s3_client, slug, images_dir, bucket_name, s3_folder_path)
    else:
        print(f"Warning: Images directory not found at {images_dir}")
    
    # Step 2.5: Copy images to output directory
    print("\n=== Step 2.5: Copying Images to Output Directory ===")
    if images_dir.exists() and images_dir.is_dir():
        copy_images_to_output(images_dir, slug_output_dir)
    else:
        print(f"Warning: Images directory not found at {images_dir}, skipping image copy")
    
    # Step 3: Update markdown with CDN URLs
    print("\n=== Step 3: Updating Markdown with CDN URLs ===")
    updated_markdown = update_markdown_images(markdown_content, slug, images_dir, cdn_base_url)
    
    # Save updated markdown
    updated_blog_file = slug_output_dir / "updated_blog.md"
    with open(updated_blog_file, 'w', encoding='utf-8') as f:
        f.write(updated_markdown)
    
    print(f"Updated blog saved to {updated_blog_file}")
    
    # Step 4: Generate LinkedIn post
    print("\n=== Step 4: Generating LinkedIn Post ===")
    linkedin_post = call_bedrock_for_linkedin_post(bedrock_client, updated_markdown, metadata, model_id)
    
    if linkedin_post and linkedin_post.strip():
        linkedin_post_file = slug_output_dir / "linkedin_post.txt"
        with open(linkedin_post_file, 'w', encoding='utf-8') as f:
            f.write(linkedin_post)
        print(f"LinkedIn post saved to {linkedin_post_file}")
    else:
        print(f"Warning: LinkedIn post generation failed or returned empty content. No file created.")
    
    # Step 5: Generate carousel content
    print("\n=== Step 5: Generating Carousel Content ===")
    carousel_content = call_bedrock_for_carousel(bedrock_client, updated_markdown, metadata, model_id)
    
    if carousel_content:
        carousel_file = slug_output_dir / "carousel.txt"
        with open(carousel_file, 'w', encoding='utf-8') as f:
            f.write(carousel_content)
        print(f"Carousel content saved to {carousel_file}")
    
    # Step 6: Generate Twitter thread
    print("\n=== Step 6: Generating Twitter Thread ===")
    twitter_thread = call_bedrock_for_twitter_thread(bedrock_client, updated_markdown, metadata, model_id)
    
    if twitter_thread:
        twitter_file = slug_output_dir / "twitter_thread.txt"
        with open(twitter_file, 'w', encoding='utf-8') as f:
            f.write(twitter_thread)
        print(f"Twitter thread saved to {twitter_file}")
    
    print("\n=== Blog Preparation Complete ===")
    print(f"Output files saved in: {slug_output_dir}")


if __name__ == "__main__":
    main()

