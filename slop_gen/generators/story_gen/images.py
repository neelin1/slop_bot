import os
from typing import List, Dict
from io import BytesIO
import logging

from slop_gen.utils.api_utils import (
    generate_openai_images_via_proxy,
    generate_images_with_imagen,
)

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


MODEL = (
    "google.imagen-3.0-generate"  # google.imagen-3.0-fast-generate, gpt-image-1, dall-e
)


def generate_single_image_from_prompt(
    prompt: str,
    output_path: str,
) -> bool:
    """
    Generates a single image using the specified prompt and saves it to output_path.
    Routes to OpenAI or Gemini Imagen based on the model name.

    Args:
        prompt: The text prompt for image generation.
        output_path: The full path where the image will be saved.
        model: The model to use (e.g., "gpt-image-1", "google.imagen-3.0-generate").
        size: The desired size for OpenAI models (e.g., "1024x1024", "1024x1536").
        quality: The quality setting for OpenAI models.

    Returns:
        True if the image was generated and saved successfully, False otherwise.
    """
    try:
        image_data_list: List[BytesIO] = []

        if MODEL.startswith("google.imagen"):
            logger.info(
                f"Using Gemini Imagen model: {MODEL} for prompt: '{prompt[:50]}...'"
            )
            # Imagen 3 uses aspect ratio, user requested 9:16 for this path.
            # The `size` and `quality` params are primarily for OpenAI.
            image_data_list = generate_images_with_imagen(
                prompt=prompt,
                model=MODEL,  # Pass the full model name e.g., "google.imagen-3.0-generate"
                number_of_images=1,
                aspect_ratio="9:16",  # looks like this aspect ratio is not supported by cornell proxy
            )
        elif MODEL.startswith("gpt-image-1"):  # doesnt work with school api key
            logger.info(f"Using OpenAI model: {MODEL} via proxy")
            image_data_list = generate_openai_images_via_proxy(
                prompt=prompt,
                model=MODEL,
                n=1,
                size="1024x1536",
                quality="medium",
                response_format="b64_json",
            )
        else:
            logger.error(
                f"Unsupported model specified: {MODEL}. Cannot generate image."
            )
            return False

        if not image_data_list:
            logger.error(
                f"No image data returned for prompt: {prompt} using model {MODEL}"
            )
            return False

        image_bytes_io = image_data_list[0]

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(image_bytes_io.getvalue())
        logger.info(f"Successfully saved image to {output_path}")
        return True

    except Exception as e:
        logger.error(
            f"Error generating or saving image for prompt '{prompt}' with model '{MODEL}': {e}"
        )
        return False


def generate_images_for_scenes(
    scene_descriptions: List[
        Dict
    ],  # Expects list of dicts from parameters["scene_descriptions"]
    base_output_dir: str,
) -> List[str]:
    """
    Generates images for a list of scene descriptions.

    Args:
        scene_descriptions: A list of dictionaries, where each dict has a 'description' key
                            containing the prompt for image generation.
        base_output_dir: The base directory where images will be saved.
                         Images will be named scene_0.png, scene_1.png, etc.
        model: The image generation model to use.
        size: The size of the images to generate.
        quality: The quality of the images to generate.

    Returns:
        A list of file paths for the successfully generated images.
    """
    generated_image_paths: List[str] = []

    if not scene_descriptions:
        logger.info("No scene descriptions provided. Skipping image generation.")
        return generated_image_paths

    os.makedirs(base_output_dir, exist_ok=True)
    logger.info(f"Ensured base output directory exists: {base_output_dir}")

    for i, scene in enumerate(scene_descriptions):
        prompt = scene.get("description")
        if not prompt:
            logger.warning(
                f"Scene {i} is missing a 'description'. Skipping image generation for this scene."
            )
            continue

        # Sanitize scene text for filename or use index
        # Using index is safer to avoid issues with special characters in scene text for filenames.
        image_filename = f"scene_{i}.png"
        output_path = os.path.join(base_output_dir, image_filename)

        logger.info(
            f"Processing scene {i+1}/{len(scene_descriptions)}: Generating image for '{prompt[:50]}...' -> {output_path}"
        )

        success = generate_single_image_from_prompt(
            prompt=prompt,
            output_path=output_path,
        )
        if success:
            generated_image_paths.append(output_path)
        else:
            logger.error(
                f"Failed to generate image for scene {i} with prompt: {prompt}"
            )

    logger.info(
        f"Finished image generation. {len(generated_image_paths)} images generated out of {len(scene_descriptions)} scenes."
    )
    return generated_image_paths
