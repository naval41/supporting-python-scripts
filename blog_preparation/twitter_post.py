from typing import Dict, Any
import re


def format_twitter_content(markdown_content: str) -> str:
    """
    Format markdown content for Twitter.
    Removes markdown markers and formats for Twitter thread.
    
    Args:
        markdown_content: Content with markdown formatting
        
    Returns:
        Formatted content suitable for Twitter
    """
    content = markdown_content
    
    # Normalize CRLF
    content = content.replace('\r\n', '\n')
    
    # Remove unsupported features (headers, links, code blocks, blockquotes, hr)
    content = re.sub(r'^#{1,6}\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'\s#{1,6}\s*', ' ', content)
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
    content = re.sub(r'```[^`]*```', '', content, flags=re.DOTALL)
    content = re.sub(r'`([^`]+)`', r'\1', content)
    content = re.sub(r'^>\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'^---+$', '', content, flags=re.MULTILINE)
    
    # Strip bold/italic markers but keep text
    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
    content = re.sub(r'__(.*?)__', r'\1', content)
    content = re.sub(r'\*(.*?)\*', r'\1', content)
    content = re.sub(r'_(.*?)_', r'\1', content)
    
    # Clean up multiple newlines
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    return content.strip()


def call_bedrock_for_twitter_thread(bedrock_client, markdown_content: str, metadata: Dict[str, Any], model_id: str) -> str:
    """
    Call Bedrock API to generate Twitter thread content.
    
    Args:
        bedrock_client: boto3 bedrock client
        markdown_content: Blog content
        metadata: Blog metadata
        model_id: Bedrock model ID
        
    Returns:
        Twitter thread content
    """
    try:
        bedrock = bedrock_client
        
        prompt = """Draft a Twitter thread for my technical blog on [topic]. Use the 1/n, 2/n format and start with a strong hook. Each tweet should explain one key concept, include actionable tips or examples, and end with a TL;DR summary plus a call to action. Keep tweets concise, add questions for engagement, and visuals if relevant.

Additional Requirements:
- Intially draft some context in a twitter thread and then start format of 1/n, 2/n, 3/n, etc.
- Format: Use 1/n, 2/n, 3/n format where n is the total number of tweets (e.g., "1/5", "2/5", etc.)
- Start with a strong hook in the first tweet that grabs attention
- Each tweet should focus on ONE key concept from the blog
- Include actionable tips or examples in each tweet
- Keep tweets concise (under 280 characters each, but prioritize clarity and readability)
- Add engagement questions where relevant to encourage interaction
- Mention visuals/diagrams if they exist in the blog content (reference image names if available)
- End with a TL;DR summary tweet that captures the main takeaway
- Include a call to action in the final tweet (e.g., read full blog at [BLOG_URL], visit Roundz.ai, etc.)
- Use [BLOG_URL] as placeholder for the blog URL if needed
- Make it conversational and engaging, suitable for Twitter/X audience
- Use emojis sparingly and appropriately (1-2 per tweet max)
- Break down complex concepts into digestible, standalone tweets

Structure:
1. Hook tweet (1/n) - Attention-grabbing opener that makes readers want to continue
2-n. Key concept tweets (2/n, 3/n, etc.) - One concept per tweet with actionable insights and examples
n-1. TL;DR summary tweet - Quick summary of the main points
n. Call to action tweet - Invite readers to read the full blog or visit Roundz.ai

Format each tweet clearly with its number (e.g., "1/n", "2/n") at the start of each tweet."""
        
        message = {
            "role": "user",
            "content": [
                {"text": f"Blog Title: {metadata.get('title', '')}"},
                {"text": f"Blog Topic: {metadata.get('title', '')}"},
                {"text": f"Blog Content:\n{markdown_content}"},
                {"text": prompt}
            ]
        }
        
        print("Calling Bedrock for Twitter thread generation...")
        
        response = bedrock.converse(
            modelId=model_id,
            messages=[message],
            inferenceConfig={
                "maxTokens": 3000,
                "temperature": 0.7
            }
        )
        
        thread_content = response['output']['message']['content'][0]['text']
        
        # Format the content for Twitter (remove markdown formatting)
        thread_content = format_twitter_content(thread_content)
        
        return thread_content
        
    except Exception as e:
        print(f"Error calling Bedrock API for Twitter thread: {e}")
        return ""

