def generate_story(num_lines=3):
    """
    Generates a short horror story with `num_lines` parts using the OpenAI API.
    Each line corresponds to one image/narration.
    """
    prompt = (
        f"Write a {num_lines}-sentence horror story. "
        "Each sentence should stand alone, be vivid and scary, and describe a moment or image. "
        "Do not use character names or background — just the moment."
    )

    messages = [
        {"role": "system", "content": "You are a horror story writer."},
        {"role": "user", "content": prompt},
    ]

    try:
        story_text = openai_chat_api(messages)
        story_lines = [line.strip() for line in story_text.split('.') if line.strip()]
        return story_lines[:num_lines]
    except Exception as e:
        print("❌ Error generating story:", e)
        return [f"Failed to generate story line {i+1}" for i in range(num_lines)]