import asyncio
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
from slop_gen.generators.story_gen.audio import generate_audio_for_scenes
from slop_gen.generators.story_gen.video import create_video_from_assets
import os
from typing import List, Optional

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
BASE_AUDIO_OUTPUT_DIR = "assets/generated_audio"
VIDEO_OUTPUT_PATH = "assets/output/final_story_video.mp4"

# alloy // deeper, serios female/high pitched male
# ash // deep male voice
# ballad // britsh male voice
# coral // female voice
# echo // standard male voice
# fable // calm male voice
# nova // standard female voice, medium high pitched
# onyx // deep, male voice, gravelly
# sage // airy female voice
# shimmer // female voice, hearty

parameters: Parameters = {
    "story": story,
    "director_prompt": "Fantasy oil painting style",
    "character_design": None,
    "video_gen": False,
    "music": True,
    "music_file": "assets/music/house_stark_theme.mp3",
    "post_processing": [PostProcessing.PAN],
    "music_volume": 0.8,
    "high_level_plan": None,
    "scene_descriptions": None,
    "image_paths": None,
    "audio_voice": "echo",
}


async def main():
    # High-level plan
    # generates a single string describing the video
    # visual style, visual flow, character design, what will be shown in major scenes, etc.

    parameters["high_level_plan"] = generate_high_level_plan(parameters)
    print(f"High-Level Plan:\n{parameters['high_level_plan']}\n")

    # Scene-bot
    # generates a list of scenes by iteratively calling the scene generation function
    # until the entire story is covered or a max iteration limit is reached.

    NUM_SCENES_PER_ITERATION = 3  # Define how many scenes to generate per call to the underlying iterative function
    MAX_ITERATIONS = (
        15  # Define a maximum number of iterations for the wrapper function
    )

    if parameters["high_level_plan"] is not None:
        print(f"Generating all scenes for the story...")
        try:
            all_generated_scenes_obj = generate_all_scenes(
                story=parameters["story"],
                high_level_plan=parameters["high_level_plan"],
                num_scenes_per_iteration=NUM_SCENES_PER_ITERATION,
                max_iterations=MAX_ITERATIONS,
            )
            parameters["scene_descriptions"] = [
                scene.model_dump() for scene in all_generated_scenes_obj
            ]  # Store as list of dicts

            print("\nGenerated Scenes:")
            if parameters["scene_descriptions"]:
                for i, scene in enumerate(parameters["scene_descriptions"]):
                    print(
                        f"  Scene {i+1}: Text: {scene['text']}, Description: {scene['description'][:60]}..."
                    )
            else:
                print("  No scenes were generated in this batch.")

        except Exception as e:
            print(f"Error during scene generation: {e}")
            return
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

        parameters["image_paths"] = await generate_images_for_scenes(
            scene_descriptions=parameters["scene_descriptions"],
            base_output_dir=BASE_IMAGE_OUTPUT_DIR,
        )
        if parameters["image_paths"]:
            print(
                f"\nSuccessfully processed {len(parameters['image_paths'])} images (original or fallback):"
            )
            for path in parameters["image_paths"]:
                print(f"  - {path}")
        else:
            print("\nNo images were generated or available after fallback.")
    else:
        print("\nSkipping image generation as no scene descriptions are available.")
        return

    # audio generation
    # generate a list of audio clips based on the text
    audio_paths_generated: Optional[List[Optional[str]]] = None
    if parameters["scene_descriptions"]:
        print(
            f"\nStarting audio generation for {len(parameters['scene_descriptions'])} scenes..."
        )
        audio_paths_generated = generate_audio_for_scenes(
            scene_descriptions=parameters["scene_descriptions"],
            output_dir=BASE_AUDIO_OUTPUT_DIR,
            voice=parameters.get("audio_voice"),
        )
        if audio_paths_generated:
            print(
                f"\nSuccessfully generated/skipped {len(audio_paths_generated)} audio files/placeholders:"
            )
            for i, path in enumerate(audio_paths_generated):
                if path:
                    print(f"  - Scene {i+1} Audio: {path}")
                else:
                    print(f"  - Scene {i+1} Audio: Skipped or Failed")
        else:
            print("\nNo audio files were generated.")
    else:
        print("\nSkipping audio generation as no scene descriptions are available.")

    # video generation
    # 2 options:
    # generate videos using sora
    # generate videos using pans
    # post-processing to add test

    # post-processing
    # merge videos and audio to create final product
    # music

    if parameters.get("image_paths") and parameters.get("scene_descriptions"):
        print("\nStarting video creation...")

        scene_texts = [
            scene.get("text", "") for scene in parameters["scene_descriptions"]
        ]

        num_scenes = len(parameters["scene_descriptions"])
        final_audio_paths_for_video: List[Optional[str]]

        if audio_paths_generated and len(audio_paths_generated) == num_scenes:
            final_audio_paths_for_video = audio_paths_generated
        else:
            if audio_paths_generated:
                print(
                    f"Warning: Audio paths list length ({len(audio_paths_generated)}) does not match scene count ({num_scenes}). Padding with None."
                )
                final_audio_paths_for_video = audio_paths_generated + [None] * (
                    num_scenes - len(audio_paths_generated)
                )
                # Ensure it does not exceed num_scenes if it was somehow longer initially (though unlikely with current audio gen logic)
                final_audio_paths_for_video = final_audio_paths_for_video[:num_scenes]
            else:
                print(
                    f"Warning: No audio paths generated. Creating silent video with {num_scenes} scenes."
                )
                final_audio_paths_for_video = [None] * num_scenes

        music_to_use = parameters["music_file"] if parameters["music"] else None
        if music_to_use and not os.path.exists(music_to_use):
            print(
                f"Warning: Music file {music_to_use} not found. Proceeding without music."
            )
            music_to_use = None

        create_video_from_assets(
            image_paths=parameters["image_paths"],
            audio_paths=final_audio_paths_for_video,
            scene_texts=scene_texts,
            output_path=VIDEO_OUTPUT_PATH,
            music_path=music_to_use,
            music_volume_param=parameters.get("music_volume"),
            post_processing_effects=parameters.get("post_processing"),
        )
    else:
        print(
            "\nSkipping video creation as image paths or scene descriptions are missing."
        )


if __name__ == "__main__":
    asyncio.run(main())
