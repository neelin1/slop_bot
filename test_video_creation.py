import os
from slop_gen.generators.story_gen.video import create_video_from_assets
from typing import List, Optional

# --- Configuration ---
NUM_SCENES = 14  # 0 to 13
BASE_IMAGE_DIR = "assets/generated_images"
BASE_AUDIO_DIR = "assets/generated_audio"
VIDEO_OUTPUT_PATH = "assets/output/test_direct_video_creation.mp4"
MUSIC_FILE = "assets/music/house_stark_theme.mp3"  # Set to None if no music or file doesn't exist
# --- End Configuration ---


def generate_test_asset_paths():
    """Generates lists of image paths, audio paths, and scene texts."""
    image_paths: List[str] = []
    audio_paths: List[Optional[str]] = []
    scene_texts: List[str] = []

    for i in range(NUM_SCENES):
        img_path = os.path.join(BASE_IMAGE_DIR, f"scene_{i}.png")
        aud_path = os.path.join(BASE_AUDIO_DIR, f"scene_audio_{i}.mp3")

        if not os.path.exists(img_path):
            print(
                f"Warning: Image file not found: {img_path}. Video generation might fail or skip this scene."
            )
            # Depending on how create_video_from_assets handles missing images,
            # you might want to skip adding it or add a placeholder if it can handle it.
            # For this test, we'll add it and let the function handle it.
        image_paths.append(img_path)

        if os.path.exists(aud_path):
            audio_paths.append(aud_path)
        else:
            print(
                f"Warning: Audio file not found: {aud_path}. Scene {i} will use default duration or be silent."
            )
            audio_paths.append(None)

        scene_texts.append(f"This is the narration for scene {i+1}.")

    return image_paths, audio_paths, scene_texts


def main():
    print("Starting direct video creation test...")

    image_paths, audio_paths, scene_texts = generate_test_asset_paths()

    if not any(
        os.path.exists(p) for p in image_paths if p
    ):  # Check if at least one image path is valid
        print("Error: No valid image paths found. Aborting test.")
        return

    print(
        f"Found {len([p for p in image_paths if os.path.exists(p)])} existing images."
    )
    print(
        f"Found {len([p for p in audio_paths if p and os.path.exists(p)])} existing audio files."
    )

    music_to_use = MUSIC_FILE
    if music_to_use and not os.path.exists(music_to_use):
        print(
            f"Warning: Music file {music_to_use} not found. Proceeding without music."
        )
        music_to_use = None

    # Ensure output directory exists
    os.makedirs(os.path.dirname(VIDEO_OUTPUT_PATH), exist_ok=True)

    print(f"Attempting to create video: {VIDEO_OUTPUT_PATH}")
    create_video_from_assets(
        image_paths=image_paths,
        audio_paths=audio_paths,
        scene_texts=scene_texts,
        output_path=VIDEO_OUTPUT_PATH,
        music_path=music_to_use,
        # You can adjust these parameters as needed for your test:
        fps=24,
        height=1080,
        music_volume=0.3,
        wrap_width=30,
        zoom_effect=True,
        default_segment_duration=3.0,
    )
    print("Video creation attempt finished.")


if __name__ == "__main__":
    # This is important for MoviePy, especially if you run into ImageMagick issues.
    # It should ideally be at the very start of your main application script.
    # However, create_video_from_assets already calls it.
    # from moviepy.config import change_settings
    # try:
    #     change_settings({"IMAGEMAGICK_BINARY": "magick"})
    # except Exception as e:
    #     print(f"Test script warning: Could not set ImageMagick binary path: {e}")

    main()
