from PIL import Image

path = "/Users/nrabadiy/IdeaProjects/RndRowsPython/scripts/image_creation/";


def overlay_logo(background_path, logo_path, output_path, padding=100):
    # Open background and logo images
    bg = Image.open(background_path)
    logo = Image.open(logo_path)

    # Get background dimensions
    bg_width, bg_height = bg.size

    print(bg_width, bg_height)

    # Get logo dimensions
    logo_width, logo_height = logo.size

    # Calculate maximum dimensions for the logo without cropping
    max_logo_width = bg_width - 2 * padding
    max_logo_height = bg_height - 2 * padding

    # Determine scaling factor
    scale_factor = min(max_logo_width / logo_width, max_logo_height / logo_height)

    # Calculate new logo size
    new_logo_width = int(logo_width * scale_factor)
    new_logo_height = int(logo_height * scale_factor)

    # Resize logo maintaining aspect ratio
    logo = logo.resize((new_logo_width, new_logo_height), Image.LANCZOS)

    # Calculate position to center the logo
    x_offset = (bg_width - new_logo_width) // 2
    y_offset = (bg_height - new_logo_height) // 2

    # Paste logo onto background
    bg.paste(logo, (x_offset, y_offset), logo if logo.mode == 'RGBA' else None)

    # Save output image as PNG
    bg.save(output_path, format="PNG")
    print(f"Image saved to {output_path}")

if __name__ == "__main__":
    overlay_logo(path+"Background_Rz.png", path+"Logo.png", "output.jpg")
