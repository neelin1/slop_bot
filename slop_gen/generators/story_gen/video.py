import os
import random
import textwrap
from typing import List, Optional

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    CompositeAudioClip,
)
from moviepy.config import change_settings

# It's good practice to call this once, e.g., in your main script or an init file if used across modules.
# However, having it here ensures it's set if this module is used somewhat independently.
# If you have a central place for such configurations, you might move it there.
try:
    change_settings({"IMAGEMAGICK_BINARY": "magick"})
except Exception as e:
    print(f"Warning: Could not set ImageMagick binary path for moviepy: {e}")
    print("TextClip rendering might be affected or slow if ImageMagick is not found.")


def create_video_from_assets(
    image_paths: List[str],
    audio_paths: List[Optional[str]],
    scene_texts: List[str],
    output_path: str = "assets/output/story_video.mp4",
    fps: int = 24,
    height: int = 1080,  # Defaulted to a common portrait height for social media
    music_path: Optional[str] = None,
    music_volume: float = 0.3,
    wrap_width: int = 30,  # Adjusted for portrait, might need tuning
    zoom_effect: bool = True,  # Added to control the zoom
    default_segment_duration: float = 3.0,  # Duration for segments with no audio
) -> None:
    clips = []

    if len(image_paths) != len(audio_paths) or len(image_paths) != len(scene_texts):
        print(
            "Error: image_paths, audio_paths, and scene_texts lists must have the same length."
        )
        # Consider raising an error or specific handling
        min_len = min(len(image_paths), len(audio_paths), len(scene_texts))
        print(f"Trimming to the shortest length: {min_len}")
        image_paths = image_paths[:min_len]
        audio_paths = audio_paths[:min_len]
        scene_texts = scene_texts[:min_len]
        if not min_len:
            print("Error: No media to process after length check.")
            return

    for i in range(len(image_paths)):
        img_path = image_paths[i]
        audio_path = audio_paths[i]
        raw_text = scene_texts[i]

        if not img_path:
            print(f"⚠️ Skipping segment {i+1} – missing image path.")
            continue

        segment_audio_clip = None
        duration = default_segment_duration

        try:
            if audio_path and os.path.exists(audio_path):
                segment_audio_clip = AudioFileClip(audio_path)
                duration = segment_audio_clip.duration
            elif raw_text == "@@@":  # Silent scene marker, use default duration
                print(
                    f"ℹ️ Segment {i+1} is silent (@@@), using default duration: {duration}s"
                )
            else:
                print(
                    f"⚠️ No audio for segment {i+1} or audio path invalid. Using default duration: {duration}s. Text: '{raw_text[:30]}...'"
                )

            # Image Clip
            img_movie_clip = (
                ImageClip(img_path).set_duration(duration).resize(height=height)
            )
            if zoom_effect:
                # Simple zoom: scales from 100% to 120% over the duration
                img_movie_clip = img_movie_clip.resize(
                    lambda t: 1 + 0.2 * (t / duration)
                )

            # Text Clip
            text_segments = []
            if (
                raw_text and raw_text != "@@@"
            ):  # Don't add text for silent scenes or if text is empty
                wrapped_text = textwrap.fill(raw_text, width=wrap_width)
                # Potentially make font, size, color, etc., parameters
                txt_clip = (
                    TextClip(
                        wrapped_text,
                        fontsize=40,  # Adjusted for 1080p height
                        font="Arial-Bold",  # Consider allowing font choice or ensure it's available
                        color="white",
                        stroke_color="black",
                        stroke_width=1,  # Changed to integer 1
                        method="caption",  # Use caption for auto-sizing to width
                        size=(
                            img_movie_clip.w * 0.9,
                            None,
                        ),  # Text width is 90% of image width
                        align="center",
                    )
                    .set_position(
                        ("center", 0.8), relative=True
                    )  # Position lower for portrait
                    .set_duration(duration)
                )
                text_segments.append(txt_clip)

            # Composite video for the segment
            video_elements = [img_movie_clip] + text_segments
            segment_video_clip = CompositeVideoClip(
                video_elements, size=(img_movie_clip.w, img_movie_clip.h)
            )

            if segment_audio_clip:
                segment_video_clip = segment_video_clip.set_audio(segment_audio_clip)

            clips.append(segment_video_clip)

        except Exception as e:
            print(f"❌ Error building segment {i+1} for image '{img_path}': {e}")

    if not clips:
        print("❌ No video segments were created. Aborting video generation.")
        return

    final_video_clip = concatenate_videoclips(clips, method="compose")

    # Add background music if specified
    if music_path and os.path.exists(music_path):
        try:
            full_music_clip = AudioFileClip(music_path)
            # If final video is longer than music, loop music, otherwise take a slice
            if final_video_clip.duration > full_music_clip.duration:
                bg_music_clip = full_music_clip.loop(  # type: ignore
                    duration=final_video_clip.duration
                ).volumex(music_volume)
            else:
                # Try to pick a somewhat random segment if music is longer
                max_start_time = max(
                    0, full_music_clip.duration - final_video_clip.duration
                )
                start_time = random.uniform(0, max_start_time)
                bg_music_clip = full_music_clip.subclip(
                    start_time, start_time + final_video_clip.duration
                ).volumex(music_volume)

            # If the final_video_clip already has audio (from segments), composite it
            if final_video_clip.audio:
                final_audio = CompositeAudioClip(
                    [final_video_clip.audio, bg_music_clip]
                )
                final_video_clip = final_video_clip.set_audio(final_audio)
            else:
                final_video_clip = final_video_clip.set_audio(bg_music_clip)
            print(f"✅ Added background music: {music_path}")
        except Exception as e:
            print(f"⚠️ Could not add background music: {e}")

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Consider adding more write_videofile parameters for quality, codec, threads, logger, etc.
        final_video_clip.write_videofile(
            output_path, fps=fps, codec="libx264", audio_codec="aac"
        )
        print(f"✅ Video successfully written to {output_path}")
    except Exception as e:
        print(f"❌ Error writing final video to {output_path}: {e}")
