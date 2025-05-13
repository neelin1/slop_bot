import re
from slop_gen.utils.api_utils import openai_chat_api


def generate_story(num_lines: int = 6) -> list[str]:
    """
    Generates a short horror story with `num_lines` parts using the OpenAI API.
    Each part is 3-9 words long, forms a simple continuing narrative,
    and evokes a vivid, scary moment. Returns a clean list of lines.
    """
    prompt = (
        f"Write a horror story in exactly {num_lines} parts. "
        "Each part should be 3-9 words long, form a simple continuing narrative, "
        "and evoke a vivid, scary image. "
        "Return exactly those parts, each on its own line, with no numbering, bullets, "
        "or extra punctuation."
    )

    messages = [
        {"role": "system", "content": "You are a horror story writer."},
        {"role": "user", "content": prompt},
    ]

    try:
        story_text = openai_chat_api(messages).strip()  # type: ignore
        raw_lines = story_text.splitlines()
        story_lines: list[str] = []

        for line in raw_lines:
            # strip any leading digits, dots, parentheses, whitespace
            clean = re.sub(r"^\s*\d+[\).\s]*", "", line).strip()
            # ignore empty or pure-digit lines
            if clean and not clean.isdigit():
                story_lines.append(clean)
            if len(story_lines) >= num_lines:
                break

        # if the model returned fewer than num_lines, pad with placeholders
        while len(story_lines) < num_lines:
            story_lines.append(f"Failed to generate story line {len(story_lines)+1}")

        return story_lines

    except Exception as e:
        print("❌ Error generating story:", e)
        return [f"Failed to generate story line {i+1}" for i in range(num_lines)]
