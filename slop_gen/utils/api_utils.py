import os
from typing import List

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
import google.generativeai as genai

# from google.generativeai import types # Keep types under genai namespace
import requests
import base64
from io import BytesIO
from PIL import Image


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_BASE_URL = "https://api.ai.it.cornell.edu/v1"
openai_client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


def generate_images_with_imagen(
    prompt, model="google.imagen-3.0-generate", number_of_images=1, aspect_ratio="3:4"
):
    """
    Generate images via the Cornell proxy's Imagen endpoint.
    Returns a list of BytesIO objects for each image.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set")

    url = f"{OPENAI_BASE_URL}/images/generations"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "num_images": number_of_images,
        "aspect_ratio": aspect_ratio,
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json().get("data", [])

    images = []
    for img in data:
        img_url = img.get("url")
        if img_url:
            img_resp = requests.get(img_url)
            img_resp.raise_for_status()
            images.append(BytesIO(img_resp.content))
        elif "b64_json" in img:
            images.append(BytesIO(base64.b64decode(img["b64_json"])))
        else:
            raise RuntimeError("No image data returned for prompt.")

    return images


def generate_openai_images_via_proxy(
    prompt: str,
    model: str = "gpt-image-1",  # Corresponds to OpenAI's GPT-4o image capabilities
    n: int = 1,
    size: str = "1024x1024",  # Default, will be overridden by caller for portrait
    quality: str = "medium",  # "standard" or "hd" for DALL-E, "low", "medium", "high" for gpt-image-1
    response_format: str = "b64_json",  # OpenAI default is b64_json or url
) -> List[BytesIO]:
    """
    Generate images using an OpenAI model (e.g., gpt-image-1) via the Cornell proxy.
    Returns a list of BytesIO objects for each image.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set")

    url = f"{OPENAI_BASE_URL}/images/generations"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "n": n,
        "size": size,
        "quality": quality,
        "response_format": response_format,
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()  # Raise an exception for HTTP errors
    data = response.json().get("data", [])

    images = []
    if not data:
        raise RuntimeError(
            f"No image data returned for prompt: {prompt}. Response: {response.text}"
        )

    for img_item in data:
        if response_format == "b64_json":
            b64_content = img_item.get("b64_json")
            if not b64_content:
                raise ValueError(
                    "b64_json format requested but no b64_json field in response item."
                )
            try:
                images.append(BytesIO(base64.b64decode(b64_content)))
            except Exception as e:
                raise ValueError(f"Failed to decode base64 content: {e}")
        elif response_format == "url":
            img_url = img_item.get("url")
            if not img_url:
                raise ValueError(
                    "url format requested but no url field in response item."
                )
            img_resp = requests.get(img_url)
            img_resp.raise_for_status()
            images.append(BytesIO(img_resp.content))
        else:
            raise ValueError(f"Unsupported response_format: {response_format}")

    if not images:
        raise RuntimeError(
            f"Image data was present but failed to process for prompt: {prompt}"
        )

    return images


def openai_chat_api(
    messages, *, model="anthropic.claude-3.5-sonnet.v2", temperature=0, seed=42
):
    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    response = client.chat.completions.create(
        messages=messages, model=model, temperature=temperature, seed=seed
    )
    return response.choices[0].message.content


def text_to_speech(
    text: str, model: str = "openai.tts-hd", voice: str = "alloy", fmt: str = "wav"
) -> bytes:
    """
    Call the Cornell proxy Audio API to synthesize `text` and return raw audio bytes.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set")

    url = f"{OPENAI_BASE_URL}/audio/speech"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "input": text, "voice": voice, "format": fmt}

    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.content


def openai_chat_api_structured(
    messages, *, model="gpt-4.1", temperature=0, seed=42, response_format=None
):
    """
    Similar to openai_chat_api, but enforces a structured output
    using the Beta OpenAI API features for structured JSON output.
    """
    # enforces schema adherence with response_format
    completion = openai_client.beta.chat.completions.parse(
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
