from typing import TypedDict, List
from slop_gen.utils.api_utils import openai_chat_api
from enum import Enum


class PostProcessing(Enum):
    PAN = 1
    CAPTION = 2
    GLITCH = 3
    PIXELATE = 4


class Parameters(TypedDict):
    """
    A TypedDict defining the input parameters for video generation.

    Attributes:
        story: The main story text.
        video_gen: If True, generate videos; otherwise, generate images with pans. Defaults to False.
        director_prompt: Optional prompt for the director.
        character_design: Optional character design input for the high-level plan.
        music: If True, include music.
        music_file: Optional path to a music file.
        post_processing: List of post-processing effects to apply to the video.
    """

    # Input Parameters
    story: str
    video_gen: bool  # optional parameter, defaults to False, if True, will generate videos, otherwise images with pans
    director_prompt: str | None  # optional parameter
    character_design: (
        str | None
    )  # optional parameter that will be inputted to high-level plan
    music: bool
    music_file: str | None
    post_processing: list[PostProcessing]

    # Output Parameters
    high_level_plan: str | None
    scene_descriptions: List[dict] | None
    image_paths: List[str] | None


def generate_high_level_plan(params: Parameters) -> str:
    """
    Generates a single string describing the high-level plan for a video.
    This plan includes visual style, visual flow, character design, and major scenes breakdown.
    """
    story_text = params["story"]
    director_prompt_text = params.get("director_prompt")
    character_design_input = params.get("character_design")

    character_design_section_prompt = "# Character Design\n"
    if character_design_input:
        character_design_section_prompt += (
            f"Describe the appearance and key visual traits of the main characters. "
            f"Incorporate the following guidelines: {character_design_input}\n"
        )
    else:
        character_design_section_prompt += "Describe the appearance and key visual traits of the main characters based on the story.\n"

    visual_style_section_prompt = "# Visual Style\n"
    if director_prompt_text:
        visual_style_section_prompt += f"Describe the overall visual style of the video. Consider the director's prompt: '{director_prompt_text}'.\n"
    else:
        visual_style_section_prompt += "Describe the overall visual style of the video, inferring from the story.\n"

    prompt_parts = [
        "You are a creative assistant helping to plan a video based on the following story.",
        "Your task is to generate a comprehensive high-level plan for the video.",
        "The plan should be a single string and use markdown # headers for each section as specified below.",
        "---",
        "Story:",
        story_text,
        "---",
        "Based on the story, and the director's vision (if provided), please generate the high-level plan with the following sections:\n",
        visual_style_section_prompt,
        "# Visual Flow",
        "How should the story unfold visually broadly?\n",
        "# Major Scenes Breakdown",
        "Briefly outline the key visual elements and actions for the major scenes in the story.",
        character_design_section_prompt,
    ]

    system_prompt = "\n".join(prompt_parts)

    messages = [
        {
            "role": "system",
            "content": "You are a creative director for video production planning. Think about what is visually interesting and how to tell the story.",
        },
        {"role": "user", "content": system_prompt},
    ]

    response_content = openai_chat_api(messages=messages, model="openai.gpt-4.1")  # type: ignore
    # model="anthropic.claude-3.7-sonnet"

    if not isinstance(response_content, str):
        # Handle cases where the API might return something unexpected, though openai_chat_api is typed to return str
        raise TypeError(
            f"Expected a string response from LLM, but got {type(response_content)}"
        )

    return response_content
