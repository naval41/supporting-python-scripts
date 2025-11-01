import boto3
import json
import os
import re
from pathlib import Path
from typing import Dict, Any
import html

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


def load_aws_config(config_file: Path) -> Dict[str, str]:
    """
    Load AWS configuration from config file.
    
    Args:
        config_file: Path to the config file
        
    Returns:
        Dictionary containing AWS configuration
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Error loading config file: {e}")
        return {}


def create_bedrock_client(config: Dict[str, str]) -> any:
    """
    Create boto3 bedrock client with credentials from config.
    
    Args:
        config: AWS configuration dictionary
        
    Returns:
        boto3 bedrock client
    """
    try:
        session = boto3.Session(
            aws_access_key_id=config.get('aws_access_key_id'),
            aws_secret_access_key=config.get('aws_secret_access_key'),
            region_name='ap-south-1'
        )
        bedrock = session.client(service_name='bedrock-runtime')
        return bedrock
    except Exception as e:
        print(f"Error creating Bedrock client: {e}")
        return None


def create_s3_client(config: Dict[str, str]) -> any:
    """
    Create boto3 S3 client with credentials from config.
    
    Args:
        config: AWS configuration dictionary
        
    Returns:
        boto3 S3 client
    """
    try:
        session = boto3.Session(
            aws_access_key_id=config.get('aws_access_key_id'),
            aws_secret_access_key=config.get('aws_secret_access_key'),
            region_name='ap-south-1'
        )
        s3 = session.client('s3')
        return s3
    except Exception as e:
        print(f"Error creating S3 client: {e}")
        return None


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
  "excerpt": "First 300 characters of the content (no HTML/markdown)",
  "slug": "url-friendly-slug",
  "time_to_read": "X min read",
  "tags": "tag1, tag2, tag3"
}

Rules:
- Title: Extract or infer the main title
- Excerpt: First 300 characters of the actual content, plain text
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
        
        prompt = """Can you draft a good LinkedIn post? I prefer a storytelling approach. I use short statements and base the post on key learnings and advice for fellow engineers. The first few lines should grab the audience's attention. I write in short statements and avoid overusing emojis. I also write in storylines—storytelling style. Start with that, but don't lose focus on the key takeaways and learnings. The first two lines should be catchy. I write key takeaways in depth: one bullet point followed by details explaining what I mean for fellow engineers. Use moderate emojis and include both detailed explanations and summaries. Use emojis for bullet points.

Write a casual, conversational post suitable for Reddit or similar communities. The tone should be friendly, approachable, and authentic—like how a real person talks in an informal setting. Use short, clear sentences and avoid overly formal or polished language. Avoid using em dashes; replace them with commas, periods, or simple conjunctions for better flow. Vary sentence structure and include natural breaks or slight imperfections that make the text feel spontaneous. Avoid repetitive patterns or phrasing that sounds AI-generated. The goal is to engage readers by sounding genuine and easy to understand.

IMPORTANT: Use **bold** and *italic* markers in the text for emphasis. Do not include markdown headers, code blocks, or inline links. Use • bullets and emojis for lists/emphasis. Produce a single LinkedIn post only.

Create a LinkedIn post based on this blog content. The post should be engaging, authentic, and encourage interaction."""
        
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
        
        post_content = response['output']['message']['content'][0]['text']
        
        # Convert markdown formatting to LinkedIn-compatible format using configured style
        post_content = format_linkedin_content(post_content)
        
        return post_content
        
    except Exception as e:
        print(f"Error calling Bedrock API for LinkedIn post: {e}")
        return ""


def main():
    """
    Main function to process blog preparation.
    """
    # Configuration
    model_id = "arn:aws:bedrock:ap-south-1:714532077139:inference-profile/apac.anthropic.claude-sonnet-4-20250514-v1:0"
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
    aws_config = load_aws_config(config_file)
    
    if not aws_config:
        print("Error: Failed to load AWS configuration")
        return
    
    # Create AWS clients
    print("Creating AWS clients...")
    bedrock_client = create_bedrock_client(aws_config)
    s3_client = create_s3_client(aws_config)
    
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
    
    if linkedin_post:
        linkedin_post_file = slug_output_dir / "linkedin_post.txt"
        with open(linkedin_post_file, 'w', encoding='utf-8') as f:
            f.write(linkedin_post)
        print(f"LinkedIn post saved to {linkedin_post_file}")
    
    print("\n=== Blog Preparation Complete ===")
    print(f"Output files saved in: {slug_output_dir}")


if __name__ == "__main__":
    main()

