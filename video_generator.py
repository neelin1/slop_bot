from slop_gen.generators.story_gen.planning import (
    Parameters,
    PostProcessing,
    generate_high_level_plan,
)
from slop_gen.generators.story_gen.scene_gen import (
    generate_all_scenes,
    SceneDescription,
)
from slop_gen.generators.story_gen.images import generate_images_for_scenes
import os

story: str = """
Depression is quiet.

Depression isn't words, it's the words we don't say.

It's telling everyone we're fine after another night of tossing and turning.

It's in the fake smile we give our mothers because truly, we can't be the ones to break her heart.

It's the questionable look from a friend.

The small push from your dog against your leg, wondering why you've been so distant.

It's in the grayish colors of my walls. The red used to burn so bright but like any other flame, they've dimmed.

It's in the lonely eyes of my sister. In the raging glare do my brother; because for some reason, he can't do anything but fight anymore.

It's the lump in our chests we can't get rid of. It's sticks to us, and weighs like wet cement. With every step we feel it shift from side to side in our hearts, swinging us off balance.

It's in the soft, broken eyes of my boyfriend. Who's smile is beginning to wear.

Depression is in the world around me. It's in the endless fighting, the killing, the shooting, the looting, the burning.

It's in every day that burns like a thousand suns. It's in the thick frosts of winter.

It's in my best friend, and the bruises her father gave to her like roses from a garden.

It's in my Father, and the bottles that collect by his bed side. It's in every cigarette, in every dismissive shake of his head.

It's in me. Inside my thoughts, in every crevice of my broken and shattered heart. It's in my words, tangling around my numb tongue crying to escape.

It's in my bed, chaining me to the spring-ridden mattress.

It's in my bathroom, in the looming reflection of my mirror.

Depression is quiet, until it's not.

Depression is simple, until it's not.

Depression is in anything and everything. . . Until it's not.
"""

BASE_IMAGE_OUTPUT_DIR = "assets/generated_images"

parameters: Parameters = {
    "story": story,
    "director_prompt": "Fantasy dark academia, oil painting style",
    "character_design": None,
    "video_gen": False,
    "music": False,
    "music_file": None,
    "post_processing": [PostProcessing.PAN, PostProcessing.CAPTION],
    "high_level_plan": None,
    "scene_descriptions": None,
    "image_paths": None,
}

# High-level plan
# generates a single string describing the video
# visual style, visual flow, character design, what will be shown in major scenes, etc.

parameters["high_level_plan"] = generate_high_level_plan(parameters)
print(f"High-Level Plan:\n{parameters['high_level_plan']}\n")

# Scene-bot
# generates a list of scenes by iteratively calling the scene generation function
# until the entire story is covered or a max iteration limit is reached.

NUM_SCENES_PER_ITERATION = 3  # Define how many scenes to generate per call to the underlying iterative function
MAX_ITERATIONS = 15  # Define a maximum number of iterations for the wrapper function

if parameters["high_level_plan"] is not None:
    print(f"Generating all scenes for the story...")
    try:
        all_generated_scenes = generate_all_scenes(
            story=parameters["story"],
            high_level_plan=parameters["high_level_plan"],
            num_scenes_per_iteration=NUM_SCENES_PER_ITERATION,
            max_iterations=MAX_ITERATIONS,
        )
        parameters["scene_descriptions"] = [
            scene.model_dump() for scene in all_generated_scenes
        ]  # Store as list of dicts

        print("\nGenerated Scenes:")
        if parameters["scene_descriptions"]:
            for i, scene in enumerate(parameters["scene_descriptions"]):
                print(f"  Scene {i+1}:")
                print(f"    Text: {scene['text']}")
                print(f"    Description: {scene['description']}")
        else:
            print("  No scenes were generated in this batch.")

    except Exception as e:
        print(f"Error during scene generation: {e}")
else:
    raise ValueError("High-level plan is missing.")

# guardrails
# ensures the text corresponds to the original story (gpt call, doesnt need exact match, but should be close), if fails will replace or add scenes to list

# image generation
# generate a list of images based on the text using 4o api
if parameters["scene_descriptions"]:
    print(
        f"\nStarting image generation for {len(parameters['scene_descriptions'])} scenes..."
    )
    # Ensure the base output directory exists
    if not os.path.exists(BASE_IMAGE_OUTPUT_DIR):
        os.makedirs(BASE_IMAGE_OUTPUT_DIR)
        print(f"Created image output directory: {BASE_IMAGE_OUTPUT_DIR}")

    parameters["image_paths"] = generate_images_for_scenes(
        scene_descriptions=parameters["scene_descriptions"],
        base_output_dir=BASE_IMAGE_OUTPUT_DIR,
    )
    if parameters["image_paths"]:
        print(f"\nSuccessfully generated {len(parameters['image_paths'])} images:")
        for path in parameters["image_paths"]:
            print(f"  - {path}")
    else:
        print("\nNo images were generated.")
else:
    print("\nSkipping image generation as no scene descriptions are available.")

# audio generation
# generate a list of audio clips based on the text

# video generation
# 2 options:
# generate videos using sora
# generate videos using pans
# post-processing to add test

# post-processing
# merge videos and audio to create final product
# music
