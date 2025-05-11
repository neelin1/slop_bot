from slop_gen.utils.api_utils import openai_chat_api

def generate_story(num_lines=3):
    """
    Generates a short horror story with `num_lines` parts using the OpenAI API.
    Each part is 3–9 words long, forms a simple continuing narrative,
    and evokes a vivid, scary moment.
    """
    prompt = (
        f"Write a horror story in {num_lines} parts. "
        "Each part should be 3–9 words long, form a simple continuing narrative, "
        "and evoke a vivid, scary image. "
        "Do not use character names or backstory—just the moment."
    )

    messages = [
        {"role": "system", "content": "You are a horror story writer."},
        {"role": "user", "content": prompt},
    ]

    try:
        story_text = openai_chat_api(messages)
        # split on newline or period, trim blanks
        story_lines = [line.strip() for line in story_text.replace('\n', '.').split('.') if line.strip()]
        return story_lines[:num_lines]
    except Exception as e:
        print("❌ Error generating story:", e)
        return [f"Failed to generate story line {i+1}" for i in range(num_lines)]
