import os
from PIL import Image
import glob

def resize_logo_with_transparency(input_path, output_path, target_size=(320, 320)):
    """
    Resize a logo to target size while maintaining transparency and aspect ratio
    """
    try:
        # Open the image
        with Image.open(input_path) as img:
            # Convert to RGBA if not already (to ensure transparency support)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Get original dimensions
            original_width, original_height = img.size
            
            # Calculate scaling factor to fit within target size while maintaining aspect ratio
            scale_factor = min(target_size[0] / original_width, target_size[1] / original_height)
            
            # Calculate new dimensions
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            # Resize the image using high-quality resampling
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create a new transparent background image of target size
            background = Image.new('RGBA', target_size, (0, 0, 0, 0))
            
            # Calculate position to center the resized logo
            x_offset = (target_size[0] - new_width) // 2
            y_offset = (target_size[1] - new_height) // 2
            
            # Paste the resized logo onto the transparent background
            background.paste(resized_img, (x_offset, y_offset), resized_img)
            
            # Save the result
            background.save(output_path, 'PNG', optimize=True)
            
            print(f"✓ Resized: {os.path.basename(input_path)} -> {new_width}x{new_height} (centered in {target_size[0]}x{target_size[1]})")
            return True
            
    except Exception as e:
        print(f"✗ Error processing {os.path.basename(input_path)}: {str(e)}")
        return False

def process_all_logos():
    """
    Process all PNG files in the logos folder and resize them to 320x320
    """
    # Define paths
    logos_dir = "logos"
    output_dir = "logos_320x320"
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Get all PNG files in the logos directory
    logo_files = glob.glob(os.path.join(logos_dir, "*.png"))
    
    if not logo_files:
        print("No PNG files found in the logos directory!")
        return
    
    print(f"Found {len(logo_files)} PNG files to process...")
    print("=" * 50)
    
    successful = 0
    failed = 0
    
    # Process each logo file
    for logo_file in logo_files:
        # Get the filename
        filename = os.path.basename(logo_file)
        
        # Create output path
        output_path = os.path.join(output_dir, filename)
        
        # Skip if it's a system file
        if filename.startswith('.'):
            print(f"Skipping system file: {filename}")
            continue
        
        # Resize the logo
        if resize_logo_with_transparency(logo_file, output_path):
            successful += 1
        else:
            failed += 1
    
    print("=" * 50)
    print(f"Processing complete!")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print(f"📁 Output directory: {output_dir}")

def main():
    """
    Main function to run the logo resizing process
    """
    print("Logo Resizer - 320x320 with Transparency")
    print("=" * 50)
    
    # Check if logos directory exists
    if not os.path.exists("logos"):
        print("Error: 'logos' directory not found!")
        print("Please make sure you're running this script from the image_creation directory.")
        return
    
    # Process all logos
    process_all_logos()

if __name__ == "__main__":
    main() 