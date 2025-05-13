import os
from typing import List, Dict, Optional
from io import BytesIO
import logging
import asyncio
import shutil

from slop_gen.utils.api_utils import (
    generate_openai_images_via_proxy,
    generate_images_with_imagen,
)

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


MODEL = (
    "google.imagen-3.0-fast-generate"
    # "google.imagen-3.0-generate"
    # "gpt-image-1"
)


async def generate_single_image_from_prompt(
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
            image_data_list = await asyncio.to_thread(
                generate_images_with_imagen,
                prompt=prompt,
                model=MODEL,  # Pass the full model name e.g., "google.imagen-3.0-generate"
                number_of_images=1,
                aspect_ratio="9:16",  # looks like this aspect ratio is not supported by cornell proxy
            )
        elif MODEL.startswith("gpt-image-1"):  # doesnt work with school api key
            logger.info(f"Using OpenAI model: {MODEL} via proxy")
            image_data_list = await asyncio.to_thread(
                generate_openai_images_via_proxy,
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

        def _write_image_to_disk():
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(image_bytes_io.getvalue())
            logger.info(f"Successfully saved image to {output_path}")

        await asyncio.to_thread(_write_image_to_disk)
        return True

    except Exception as e:
        logger.error(
            f"Error generating or saving image for prompt '{prompt}' with model '{MODEL}': {e}"
        )
        return False


async def generate_images_for_scenes(
    scene_descriptions: List[
        Dict
    ],  # Expects list of dicts from parameters["scene_descriptions"]
    base_output_dir: str,
) -> List[str]:
    """
    Generates images for a list of scene descriptions asynchronously, with fallback for failures.
    If an image fails to generate, it attempts to use the previous image, or the next if the first fails.

    Args:
        scene_descriptions: A list of dictionaries, where each dict has a 'description' key
                            containing the prompt for image generation.
        base_output_dir: The base directory where images will be saved.
                         Images will be named scene_0.png, scene_1.png, etc.

    Returns:
        A list of file paths for images that are present (either original or fallback).
    """
    if not scene_descriptions:
        logger.info("No scene descriptions provided. Skipping image generation.")
        return []

    os.makedirs(base_output_dir, exist_ok=True)
    logger.info(f"Ensured base output directory exists: {base_output_dir}")

    tasks = []
    # Store the intended final output path for each scene, even if initially skipped.
    intended_output_paths = [
        os.path.join(base_output_dir, f"scene_{i}.png")
        for i in range(len(scene_descriptions))
    ]

    for i, scene in enumerate(scene_descriptions):
        prompt = scene.get("description")
        output_path_for_generation_attempt = intended_output_paths[i]

        if not prompt:
            logger.warning(
                f"Scene {i} ('{output_path_for_generation_attempt}') is missing a 'description'. Scheduling as a failed task."
            )
            # Add a dummy completed task returning False for scenes missing descriptions
            tasks.append(asyncio.sleep(0, result=False))
            continue

        logger.info(
            f"Queueing scene {i+1}/{len(scene_descriptions)}: Generating image for '{prompt[:50]}...' -> {output_path_for_generation_attempt}"
        )
        task = generate_single_image_from_prompt(
            prompt=prompt,
            output_path=output_path_for_generation_attempt,  # Use the final intended path for the attempt
        )
        tasks.append(task)

    if not tasks:  # All scenes might have been skipped (e.g., all had no descriptions)
        logger.info("No valid scenes to process for image generation.")
        return []

    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    success_flags = [False] * len(tasks)
    # initially_successful_paths will store the path if the direct generation was a success.
    initially_successful_paths: List[Optional[str]] = [None] * len(tasks)

    for i, result_or_exc in enumerate(raw_results):
        current_path_attempted = intended_output_paths[i]

        if isinstance(result_or_exc, Exception):
            logger.error(
                f"Task for {current_path_attempted} failed with an unhandled exception: {result_or_exc}"
            )
            success_flags[i] = False
        elif result_or_exc is True:
            logger.info(f"Successfully generated {current_path_attempted}")
            success_flags[i] = True
            initially_successful_paths[i] = current_path_attempted
        else:  # result_or_exc is False (can also be from our dummy asyncio.sleep for skipped prompts)
            # If it was a real generation that returned False, generate_single_image_from_prompt logged it.
            # If it was a skipped prompt, we logged it when creating the dummy task.
            if scene_descriptions[i].get(
                "description"
            ):  # Only log this if it was a real attempt
                logger.warning(
                    f"Generation/saving for {current_path_attempted} failed (returned False). See previous logs."
                )
            success_flags[i] = False

    final_image_paths: List[Optional[str]] = [None] * len(tasks)

    for i in range(len(tasks)):
        current_target_path = intended_output_paths[i]  # This is the scene_i.png path

        if success_flags[i]:
            final_image_paths[i] = initially_successful_paths[i]
        else:
            logger.info(
                f"Attempting to find fallback for failed/skipped image: {current_target_path}"
            )
            fallback_source_path: Optional[str] = None

            if i == 0:
                for j in range(i + 1, len(tasks)):
                    if success_flags[j] and initially_successful_paths[j]:
                        fallback_source_path = initially_successful_paths[j]
                        logger.info(
                            f"Found forward fallback for {current_target_path}: {fallback_source_path}"
                        )
                        break
                if not fallback_source_path:
                    logger.warning(
                        f"No subsequent successful image to use as fallback for {current_target_path}"
                    )
            else:
                for j in range(i - 1, -1, -1):
                    if final_image_paths[
                        j
                    ]:  # Check if image j (original or already a resolved fallback) exists
                        fallback_source_path = final_image_paths[j]
                        logger.info(
                            f"Found backward fallback for {current_target_path}: {fallback_source_path}"
                        )
                        break
                if not fallback_source_path:
                    logger.warning(
                        f"No preceding image (original or fallback) to use as fallback for {current_target_path}"
                    )

            if fallback_source_path:
                try:
                    await asyncio.to_thread(
                        shutil.copy, fallback_source_path, current_target_path
                    )
                    final_image_paths[i] = current_target_path
                    logger.info(
                        f"Successfully used fallback: Copied {fallback_source_path} to {current_target_path}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error copying fallback from {fallback_source_path} to {current_target_path}: {e}"
                    )
            else:
                logger.warning(
                    f"No fallback image available for {current_target_path}. It will be missing."
                )

    actual_final_paths: List[str] = [p for p in final_image_paths if p is not None]

    logger.info(
        f"Finished image generation processing. {len(actual_final_paths)} images are present out of {len(scene_descriptions)} scenes attempted."
    )
    return actual_final_paths
