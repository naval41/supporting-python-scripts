# Blog Preparation Script

This script automates blog preparation tasks including metadata extraction, image upload to S3, and LinkedIn post generation.

## Features

1. **Metadata Extraction**: Extracts blog title, excerpt, slug, reading time, and tags using Bedrock
2. **Image Upload**: Uploads images to S3 in a slug-named folder
3. **CDN URL Updates**: Updates markdown image references with CDN URLs
4. **LinkedIn Post Generation**: Creates a LinkedIn post based on blog content

## Prerequisites

- AWS credentials (access key and secret key)
- boto3 library installed
- Access to AWS Bedrock with Anthropic Sonnet 4 model
- S3 bucket with appropriate permissions

## Setup

1. Create AWS credentials config file:
   ```bash
   cp aws_config.json.example aws_config.json
   ```
   
2. Edit `aws_config.json` and add your AWS credentials:
   ```json
   {
     "aws_access_key_id": "YOUR_AWS_ACCESS_KEY_ID",
     "aws_secret_access_key": "YOUR_AWS_SECRET_ACCESS_KEY"
   }
   ```

3. Place your blog markdown file in the `input/` directory

4. Create an `images/` folder inside `input/` and add all images there

5. Update the configuration in the script (if needed):
   - `bucket_name`: Your S3 bucket name (already set to `roundz-static-asset-prod`)
   - `s3_folder_path`: Your S3 folder path (already set to `static-asset/blog_images/`)

## Directory Structure

```
scripts/blog_preparation/
├── input/
│   ├── your_blog_post.md
│   └── images/
│       ├── image1.png
│       ├── image2.jpg
│       └── ...
├── output/
│   └── {slug}/
│       ├── metadata.json
│       ├── updated_blog.md
│       └── linkedin_post.txt
├── aws_config.json
├── blog_preparation.py
├── fix_image_metadata.py
└── README.md
```

## Usage

```bash
cd scripts/blog_preparation
python blog_preparation.py
```

## Output Files

The script generates the following files in the `output/{slug}/` folder:

1. **metadata.json**: Contains blog metadata
   - Title
   - Excerpt (300 chars)
   - Slug
   - Time to read
   - Tags

2. **updated_blog.md**: Markdown with CDN URLs for images
   - All image references updated to use CDN URLs
   - Format: `https://d5osvdbc8um23.cloudfront.net/static-asset/blog_images/{slug}/{image_name}`

3. **linkedin_post.txt**: Generated LinkedIn post content

**Note**: All output files are organized by slug in separate subdirectories under `output/`.

## Configuration

The script is pre-configured with:
- **Region**: ap-south-1 (Mumbai)
- **Bucket**: roundz-static-asset-prod
- **S3 Path**: static-asset/blog_images/
- **CDN**: https://d5osvdbc8um23.cloudfront.net/static-asset/blog_images/

To change configuration, edit these variables in `blog_preparation.py` (lines 265-268):

```python
model_id = "arn:aws:bedrock:us-east-1:339713139204:inference-profile/us.anthropic.claude-3-5-sonnet-20240620-v1:0"
bucket_name = "roundz-static-asset-prod"
s3_folder_path = "static-asset/blog_images/"
cdn_base_url = "https://d5osvdbc8um23.cloudfront.net/static-asset/blog_images/"
```

## Notes

- The script uses Anthropic Sonnet 4 via AWS Bedrock
- Images should be in common formats: .jpg, .jpeg, .png, .gif, .webp, .svg
- Ensure your AWS credentials have permissions for S3 upload and Bedrock access
- Region is set to ap-south-1 (Mumbai)
- Keep `aws_config.json` secure and never commit it to version control
- **Important**: Images are uploaded with correct Content-Type metadata to ensure browsers display them instead of downloading

### Troubleshooting: Images Not Displaying

If images uploaded previously are downloading instead of displaying:

1. **Quick fix using helper script**: 
   ```bash
   python fix_image_metadata.py
   ```
   Enter the slug when prompted, and it will update all images in that folder.

2. **Re-upload using the main script**: Simply run the script again - it now sets the correct Content-Type

3. **Manual fix in AWS Console**:
   - Go to S3 bucket → navigate to the image
   - Click on the object → Properties → Metadata
      - Edit the metadata to add `Content-Type` with appropriate value:
     - `.jpg`, `.jpeg` → `image/jpeg`
     - `.png` → `image/png`
     - `.gif` → `image/gif`
     - `.webp` → `image/webp`
     - `.svg` → `image/svg+xml`

### Content-Type Mapping

The script now automatically sets the correct Content-Type when uploading:
- `.jpg`, `.jpeg` → `image/jpeg`
- `.png` → `image/png`
- `.gif` → `image/gif`
- `.webp` → `image/webp`
- `.svg` → `image/svg+xml`

