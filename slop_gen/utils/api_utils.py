import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from google import genai
from google.genai import types


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def generate_images_with_imagen(
    prompt, *, model="imagen-3.0-generate-002", number_of_images=1, aspect_ratio="1:1"
):
    """
    Generate images using Google Cloud's Imagen 3 API.

    Args:
        prompt (str): The text prompt for image generation.
        model (str, optional): The Imagen model to use. Defaults to "imagen-3.0-generate-002".
        number_of_images (int, optional): Number of images to generate (1-4). Defaults to 1.
        aspect_ratio (str, optional): Aspect ratio of generated images.
                                    Supported values: "1:1", "3:4", "4:3", "9:16", "16:9".
                                    Defaults to "1:1".

    Returns:
        list: List of generated image objects that can be accessed for image data.
              Each object has a 'image' attribute with 'image_bytes' that can be used
              with PIL's Image.open(BytesIO(image_bytes)) to display or save.
    """
    if GEMINI_API_KEY is None:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    if not 1 <= number_of_images <= 4:
        raise ValueError("number_of_images must be between 1 and 4")

    valid_aspect_ratios = ["1:1", "3:4", "4:3", "9:16", "16:9"]
    if aspect_ratio not in valid_aspect_ratios:
        raise ValueError(f"aspect_ratio must be one of {valid_aspect_ratios}")

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_images(
        model=model,
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=number_of_images, aspect_ratio=aspect_ratio
        ),
    )

    return response.generated_images


def openai_chat_api(messages, *, model="gpt-4o", temperature=0, seed=42):
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        messages=messages, model=model, temperature=temperature, seed=seed
    )
    return response.choices[0].message.content


def openai_chat_api_structured(
    messages, *, model="gpt-4o", temperature=0, seed=42, response_format=None
):
    """
    Similar to openai_chat_api, but enforces a structured output
    using the Beta OpenAI API features for structured JSON output.
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    # enforces schema adherence with response_format
    completion = client.beta.chat.completions.parse(
        messages=messages,
        model=model,
        temperature=temperature,
        seed=seed,
        response_format=response_format,  # type: ignore
    )

    structured_response = completion.choices[0].message
    # Catch refusals
    if structured_response.refusal:
        raise ValueError(
            "OpenAI refused to complete input: " + structured_response.refusal
        )
    elif structured_response.parsed:
        return structured_response.parsed
    else:
        raise ValueError("No structured output or refusal was returned.")
