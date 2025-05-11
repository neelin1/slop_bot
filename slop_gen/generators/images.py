import os
from PIL import Image
from slop_gen.utils.api_utils import generate_images_with_imagen
import requests
import base64
from io import BytesIO

def generate_images(lines, output_dir="assets/images"):
    """
    Generates and saves one image per story line.
    Returns a list of file paths (or None on failure).
    """
    os.makedirs(output_dir, exist_ok=True)
    saved_paths = []

    for idx, line in enumerate(lines):
        try:
            img_streams = generate_images_with_imagen(prompt=line)
            image = Image.open(img_streams[0])
            path = os.path.join(output_dir, f"image_{idx+1}.png")
            image.save(path)
            saved_paths.append(path)
        except Exception as e:
            print(f"❌ Failed to generate image for line {idx+1}: {e}")
            saved_paths.append(None)

    return saved_paths