from PIL import Image, ImageOps
import os

path = "/Users/nrabadiy/IdeaProjects/RndRowsPython/scripts/image_creation/"

def create_background(image_path, width=1500, height=1000, color=(0, 0, 0)):
    """Creates a solid black background image."""
    bg = Image.new("RGB", (width, height), color)
    bg.save(image_path, format="PNG")
    print(f"Background image created and saved to {image_path}")


def convert_logo_to_gray(logo_path, output_path, gray_color=(200, 200, 200)):
    """Converts non-transparent parts of the logo to a single light grayish color."""
    logo = Image.open(logo_path).convert("RGBA")
    data = logo.getdata()

    new_data = []
    for item in data:
        if item[3] > 0:  # If pixel is not transparent
            new_data.append((*gray_color, item[3]))  # Apply gray color but keep original transparency
        else:
            new_data.append(item)  # Keep transparent pixels unchanged

    logo.putdata(new_data)
    logo.save(output_path, format="PNG")
    print(f"Logo converted to gray and saved to {output_path}")


def overlay_logo(background_path, logo_path, output_path, padding=100):
    """Overlays the gray logo on a black background, centering it."""
    bg = Image.open(background_path).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")

    # Get dimensions
    bg_width, bg_height = bg.size
    logo_width, logo_height = logo.size

    # Scale logo while maintaining aspect ratio
    max_logo_width = bg_width - 2 * padding
    max_logo_height = bg_height - 2 * padding
    scale_factor = min(max_logo_width / logo_width, max_logo_height / logo_height)
    new_logo_size = (int(logo_width * scale_factor), int(logo_height * scale_factor))
    logo = logo.resize(new_logo_size, Image.LANCZOS)

    # Position logo at center
    x_offset = (bg_width - new_logo_size[0]) // 2
    y_offset = (bg_height - new_logo_size[1]) // 2

    # Merge images
    combined = Image.new("RGBA", bg.size)
    combined.paste(bg, (0, 0))
    combined.paste(logo, (x_offset, y_offset), logo)
    combined.save(output_path, format="PNG")
    print(f"Final image saved to {output_path}")


def process_logo_folder(logo_folder, output_folder, background_path):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(logo_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            logo_path = os.path.join(logo_folder, filename)
            gray_logo_path = os.path.join(output_folder, f"gray_{filename}")
            output_path = os.path.join(output_folder, f"final_{filename}")

            convert_logo_to_gray(logo_path, gray_logo_path)
            overlay_logo(background_path, gray_logo_path, output_path)


if __name__ == "__main__":
    bg_path = "background.png"
    create_background(bg_path)
    process_logo_folder(path+"logos", path+"gray_outputs", bg_path)
