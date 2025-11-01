from PIL import Image

path = "/Users/nrabadiy/IdeaProjects/RndRowsPython/scripts/image_creation/"
import os
from PIL import Image


def create_background(image_path, width=1500, height=1000, color="#3d3d3d"):
    # Create a new image with the given color
    bg = Image.new("RGB", (width, height), color)
    bg.save(image_path, format="PNG")
    print(f"Background image created and saved to {image_path}")


def overlay_logo(background_path, logo_path, output_path, padding=100):
    # Open background and logo images
    bg = Image.open(background_path).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")

    # Get background dimensions
    bg_width, bg_height = bg.size

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

    # Create transparent layer to handle logo transparency
    combined = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    combined.paste(bg, (0, 0))

    # Calculate position to center the logo
    x_offset = (bg_width - new_logo_width) // 2
    y_offset = (bg_height - new_logo_height) // 2

    # Paste logo onto background handling transparency correctly
    combined.paste(logo, (x_offset, y_offset), logo)

    # Save output image as PNG
    combined.save(output_path, format="PNG")
    print(f"Image saved to {output_path}")


def process_logo_folder(logo_folder, output_folder, background_path):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(logo_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            logo_path = os.path.join(logo_folder, filename)
            output_path = os.path.join(output_folder, f"{filename}")
            overlay_logo(background_path, logo_path, output_path)

if __name__ == "__main__":
    #create_background("background.png")
    process_logo_folder(path+"logos", path+"outputs_bgp", path+"Background_Rz.png")
