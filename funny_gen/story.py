import re
from slop_gen.utils.api_utils import openai_chat_api

def generate_funny_story(num_lines: int = 6) -> list[str]:
    """
    Generates a short funny story with `num_lines` parts using the OpenAI API.
    Each part is 3–9 words long, forms a simple continuing narrative,
    and delivers light-hearted or humorous moments.
    """
    prompt = (
        f"Write a short funny story in exactly {num_lines} parts. "
        "Each part should be 3–9 words long, form a simple continuing narrative, "
        "and be light-hearted or humorous. Think absurd, ironic, or silly. "
        "Return each part on its own line, with no bullets or numbering."
    )

    messages = [
        {"role": "system", "content": "You are a comedic story writer."},
        {"role": "user", "content": prompt},
    ]

    try:
        story_text = openai_chat_api(messages).strip()
        raw_lines = story_text.splitlines()
        story_lines = []

        for line in raw_lines:
            clean = re.sub(r'^\s*\d+[\).\s]*', '', line).strip()
            if clean and not clean.isdigit():
                story_lines.append(clean)
            if len(story_lines) >= num_lines:
                break

        while len(story_lines) < num_lines:
            story_lines.append(f"Failed to generate story line {len(story_lines)+1}")

        return story_lines

    except Exception as e:
        print("❌ Error generating story:", e)
        return [f"Failed to generate story line {i+1}" for i in range(num_lines)]
