import os
from PIL import Image
from io import BytesIO
from slop_gen.utils.api_utils import generate_images_with_imagen

def generate_images(lines, output_dir="assets/images"):
    """
    Generates one image per story line using Google's Imagen 3.

    Args:
        lines (list[str]): List of story lines.
        output_dir (str): Directory to save images (default: assets/images).

    Returns:
        list[str]: List of file paths to the generated images.
    """
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []

    for i, line in enumerate(lines):
        try:
            imgs = generate_images_with_imagen(
                prompt=line,
                number_of_images=1,
                aspect_ratio="3:4"
            )
            img_bytes = imgs[0].image.image_bytes
            image = Image.open(BytesIO(img_bytes))
            image_path = os.path.join(output_dir, f"image_{i+1}.png")
            image.save(image_path)
            image_paths.append(image_path)
        except Exception as e:
            print(f"❌ Failed to generate image for line {i+1}: {e}")
            image_paths.append(None)

    return image_paths
