from typing import List, Optional
from pydantic import BaseModel
from slop_gen.utils.api_utils import openai_chat_api_structured


class SceneDescription(BaseModel):
    """
    Represents a single scene with its corresponding text from the story
    and a detailed description for image generation.
    """

    text: str  # Original text from the story covered by this scene
    description: str  # Detailed prompt for image generation for this scene


class SceneList(BaseModel):
    """
    A list of scene descriptions.
    """

    scenes: List[SceneDescription]


def generate_scenes_iteratively(
    story: str,
    high_level_plan: str,
    num_scenes_to_generate: int,
    existing_scenes: Optional[List[SceneDescription]] = None,
) -> SceneList:
    """
    Generates a batch of scene descriptions based on the story, high-level plan,
    and any existing scenes.

    Args:
        story: The full text of the story.
        high_level_plan: The overall plan for the video's visual style, flow, etc.
        num_scenes_to_generate: The target number of new scenes to generate in this batch.
        existing_scenes: A list of scenes already generated, to provide context.

    Returns:
        A SceneList object containing the newly generated scenes.
    """
    if existing_scenes is None:
        existing_scenes = []

    prompt_parts = [
        "You are a scene generation assistant. Your task is to break down a story into a series of scenes, each with a text segment from the story and a detailed image generation prompt.",
        "You will be given the full story, a high-level visual plan, and any scenes already generated.",
        "Your goal is to generate the *next* batch of scenes, up to a specified number.",
        "Ensure that the scenes text is a direct segment of the original story. Do NOT paraphrase or create new text. Ensure continuity with the previous scene's text if applicable.",
        "Ensure that the text follows the story's. The first scene should match the first text in the story and the last scene the last text. When you generate a new batch, the text should be a continuation of the previous scene's text.",
        "---",
        "Full Story:",
        story,
        "---",
        "High-Level Visual Plan:",
        high_level_plan,
        "---",
    ]

    if existing_scenes:
        prompt_parts.append(
            "Existing Scenes (already generated, continue from where these left off):"
        )
        for i, scene in enumerate(existing_scenes):
            prompt_parts.append(f"  Scene {i+1} Text: {scene.text}")
            prompt_parts.append(f"  Scene {i+1} Description: {scene.description}")
        last_scene_text = existing_scenes[-1].text
        if last_scene_text == "DONE":
            return SceneList(scenes=[SceneDescription(text="DONE", description="DONE")])
        prompt_parts.append(
            f"""---
IMPORTANT: The last generated scene covered the text: "{last_scene_text}". Focus on the part of the story that IMMEDIATELY FOLLOWS this text for the new scenes."""
        )
    else:
        prompt_parts.append("This is the first batch of scenes.")

    prompt_parts.extend(
        [
            "---",
            f"Please generate up to {num_scenes_to_generate} new scenes.",
            "Key Instructions for Generating Scenes:",
            "1. 'text': This field MUST be a direct segment of the original story. Do NOT paraphrase or create new text. Ensure continuity with the previous scene's text if applicable.",
            "2. 'description': This field should be a DETAILED prompt for an AI image generator. It should vividly describe the visual elements, characters, setting, mood, and action for the scene based on its 'text' and the 'High-Level Visual Plan' It should expliticly mention the art style as explicated in the 'High-Level Visual Plan'.",
            "3. Scene Length: Scenes do not have to be of uniform length. Some story segments might naturally form shorter scenes, others longer ones. Focus on capturing meaningful narrative beats.",
            "4. Adherence to Story: Do NOT invent new story elements or create scenes that are not supported by the provided story text.",
            "5. Reaching Target Number: It is perfectly acceptable to generate FEWER than {num_scenes_to_generate} scenes if the story is concluding or if the remaining story text naturally breaks into fewer scenes. Do not force extra scenes or make up content to reach the target number, especially near the end of the story.",
            "6. Iteration: You are generating a *batch*. If the story is not fully covered, more scenes will be generated in a subsequent call.",
            "7. IMPORTANT - Signaling Completion: If you determine that the *entire story* has been covered by the combination of existing scenes and the new scenes you are generating in this batch, the VERY LAST scene in your list of scenes for *this batch* should have its 'text' field set to EXACTLY 'DONE' and its 'description' field set to EXACTLY 'DONE'. Do not include any other scenes after this 'DONE' signal scene.",
            "8. Silent Scenes: If you want a scene to have no voice-over (e.g., for a visual montage with music), set the 'text' field to '@@@'. Each '@' symbol will represent approximately a half-second pause. For example, '@@' would be a 1-second pause, '@@@@' would be a 2-second pause. The 'description' field should still detail the visuals for this silent scene.",
            "Respond with a list of scene objects, where each object has a 'text' field and a 'description' field.",
        ]
    )

    system_prompt = "\n".join(prompt_parts)

    messages = [
        {
            "role": "system",
            "content": "You are an expert at breaking down stories into visually descriptive scenes for video production, adhering strictly to provided schemas and instructions.",
        },
        {"role": "user", "content": system_prompt},
    ]

    response = openai_chat_api_structured(
        messages=messages,
        response_format=SceneList,
        model="openai.gpt-4.1-mini",
    )

    if not isinstance(response, SceneList):
        raise TypeError(f"Expected SceneList response, got {type(response)}")

    return response


def generate_all_scenes(
    story: str,
    high_level_plan: str,
    num_scenes_per_iteration: int,
    max_iterations: int = 10,  # Default max iterations to prevent infinite loops
) -> List[SceneDescription]:
    """
    Generates all scenes for a story by iteratively calling generate_scenes_iteratively
    until the story is fully covered or max_iterations is reached.

    Args:
        story: The full text of the story.
        high_level_plan: The overall plan for the video's visual style, flow, etc.
        num_scenes_per_iteration: The target number of new scenes to generate per iteration.
        max_iterations: The maximum number of iterations to prevent infinite loops.

    Returns:
        A list of SceneDescription objects covering the entire story.
    """
    all_scenes: List[SceneDescription] = []
    current_iteration = 0

    while current_iteration < max_iterations:
        print(f"Scene generation iteration {current_iteration + 1}...")
        new_scene_list_obj = generate_scenes_iteratively(
            story=story,
            high_level_plan=high_level_plan,
            num_scenes_to_generate=num_scenes_per_iteration,
            existing_scenes=all_scenes if all_scenes else None,
        )

        if not new_scene_list_obj.scenes:
            print(
                "No new scenes generated, assuming story is complete or an issue occurred."
            )
            break  # Exit if no new scenes are returned

        # Check if the last scene is the "DONE" signal
        last_scene_in_batch = new_scene_list_obj.scenes[-1]
        if (
            last_scene_in_batch.text == "DONE"
            and last_scene_in_batch.description == "DONE"
        ):
            # Add all scenes from this batch except the "DONE" signal
            all_scenes.extend(new_scene_list_obj.scenes[:-1])
            print("'DONE' signal received. Story fully processed.")
            break
        else:
            all_scenes.extend(new_scene_list_obj.scenes)

        current_iteration += 1
        if current_iteration >= max_iterations:
            print(
                f"Reached maximum iterations ({max_iterations}). Stopping scene generation."
            )
            break

        # Safety break if the story seems to be looping on the same text, indicating a possible issue
        # This is a basic check; more sophisticated checks might be needed.
        if (
            len(all_scenes) > num_scenes_per_iteration
        ):  # Ensure there's enough history to check
            if all_scenes[-1].text == all_scenes[-1 - num_scenes_per_iteration].text:
                print(
                    "Warning: Scene generation might be stuck on the same text. Breaking to prevent infinite loop."
                )
                break

    return all_scenes
