import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
import google.generativeai as genai
from google.generativeai import types
import requests
import base64
from io import BytesIO
from PIL import Image


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_BASE_URL = "https://api.ai.it.cornell.edu/v1"


def generate_images_with_imagen(
    prompt,
    model="google.imagen-3.0-generate",
    number_of_images=1,
    aspect_ratio="3:4"
):
    """
    Generate images via the Cornell proxy’s Imagen endpoint.
    Returns a list of BytesIO objects for each image.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set")

    url = f"{OPENAI_BASE_URL}/images/generations"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "num_images": number_of_images,
        "aspect_ratio": aspect_ratio
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


def openai_chat_api(messages, *, model="anthropic.claude-3.5-sonnet.v2", temperature=0, seed=42):
    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    response = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature,
        seed=seed
    )
    return response.choices[0].message.content

    
    
def text_to_speech(
    text: str,
    model: str = "openai.tts-hd",
    voice: str = "alloy",
    fmt: str = "wav"
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
    payload = {
        "model": model,
        "input": text,
        "voice": voice,
        "format": fmt
    }

    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.content
    
    



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