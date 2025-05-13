import os
import random
import textwrap
from typing import List, Optional, Callable

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


# --- Pan and Zoom Effect Functions ---
# Base scale factor - always start at least this zoomed in.
# (relative to the image covering the main dimension of the frame).
S_BASE = 1.2
# Delta scale factor - how much the zoom changes during the effect.
S_DELTA = 0.1


def zoom_in_effect(
    clip: ImageClip, duration: float, frame_W: int, frame_H: int
) -> ImageClip:
    """Zooms in (e.g., 120% to 130%) and centers the content."""
    scale_func = lambda t: S_BASE + S_DELTA * (t / duration)
    return clip.resize(scale_func).set_position("center", "center")


def zoom_out_effect(
    clip: ImageClip, duration: float, frame_W: int, frame_H: int
) -> ImageClip:
    """Zooms out (e.g., 130% to 120%) and centers the content."""
    scale_func = lambda t: (S_BASE + S_DELTA) - S_DELTA * (t / duration)
    return clip.resize(scale_func).set_position("center", "center")


def zoom_in_top_right_effect(
    clip: ImageClip, duration: float, frame_W: int, frame_H: int
) -> ImageClip:
    """Zooms in, keeping the top-right corner of the content fixed relative to the frame."""
    W_clip = clip.w  # Original width of the clip (which is frame_H for square images)
    scale_func = lambda t: S_BASE + S_DELTA * (t / duration)

    def position_func(t):
        s = scale_func(t)
        # Calculate x so that scaled clip's right edge (x + s*W_clip) aligns with frame_W
        x_pos = frame_W - (s * W_clip)
        y_pos = 0  # Keep top edge aligned with frame's top
        return (x_pos, y_pos)

    return clip.resize(scale_func).set_position(position_func)


def zoom_out_top_right_effect(
    clip: ImageClip, duration: float, frame_W: int, frame_H: int
) -> ImageClip:
    """Zooms out, keeping the top-right corner of the content fixed relative to the frame."""
    W_clip = clip.w  # Original width of the clip
    scale_func = lambda t: (S_BASE + S_DELTA) - S_DELTA * (t / duration)

    def position_func(t):
        s = scale_func(t)
        x_pos = frame_W - (s * W_clip)
        y_pos = 0
        return (x_pos, y_pos)

    return clip.resize(scale_func).set_position(position_func)


# Pan effects would also need to accept frame_W, frame_H and be adjusted
# def pan_left_effect(clip: ImageClip, duration: float, frame_W: int, frame_H: int) -> ImageClip:
#     """Pans from right to left."""
#     # Initial clip is frame_H x frame_H. We want to make it wider for panning.
#     zoomed_clip = clip.resize(width=clip.w * S_BASE) # e.g. 1.2x wider
#     # Vertically center the zoomed_clip within the frame_H
#     y_pos = (frame_H - zoomed_clip.h) / 2
#
#     def pos_pan_left(t):
#         # Start: zoomed_clip's left edge at frame's left (0).
#         # End: zoomed_clip's right edge at frame's right (frame_W).
#         # So, zoomed_clip's left moves from 0 to frame_W - zoomed_clip.w.
#         start_x = 0
#         end_x = frame_W - zoomed_clip.w
#         current_x = start_x + (end_x - start_x) * (t / duration)
#         return (current_x, y_pos)
#
#     return zoomed_clip.set_position(pos_pan_left)
#
# def pan_right_effect(clip: ImageClip, duration: float, frame_W: int, frame_H: int) -> ImageClip:
#     """Pans from left to right."""
#     zoomed_clip = clip.resize(width=clip.w * S_BASE)
#     y_pos = (frame_H - zoomed_clip.h) / 2
#
#     def pos_pan_right(t):
#         start_x = frame_W - zoomed_clip.w
#         end_x = 0
#         current_x = start_x + (end_x - start_x) * (t / duration)
#         return (current_x, y_pos)
#     return zoomed_clip.set_position(pos_pan_right)


# List of available effects
# For now, let's stick to zoom effects as panning needs more careful implementation
# with respect to image and frame sizes.
# Will refine panning later if needed.
# available_effects: List[Callable[[ImageClip, float], ImageClip]] = [
#     zoom_in_effect,
#     zoom_out_effect,
#     # pan_left_effect, # Disabled for now
#     # pan_right_effect # Disabled for now
# ]
# Simpler approach for now, will add more sophisticated pans if these are not enough.
available_effects: List[Callable[[ImageClip, float, int, int], ImageClip]] = [
    zoom_in_effect,
    zoom_out_effect,
    zoom_in_top_right_effect,
    zoom_out_top_right_effect,
    # pan_left_effect, # Disabled for now
    # pan_right_effect # Disabled for now
]


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
    total_segments = len(image_paths)

    # Calculate target 9:16 frame dimensions
    target_frame_H = height
    target_frame_W = int(round(target_frame_H * 9 / 16))
    if target_frame_W % 2 != 0:  # Ensure width is even for some codecs
        target_frame_W += 1

    print(f"Target video resolution: {target_frame_W}x{target_frame_H} (9:16)")

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

            # Image Clip: resize to cover frame height (making it square HxH), then apply effects
            img_movie_clip_base = (
                ImageClip(img_path)
                .set_duration(duration)
                .resize(
                    height=target_frame_H
                )  # Image becomes target_frame_H x target_frame_H
            )

            if zoom_effect:
                if available_effects:
                    effect_func = random.choice(available_effects)
                    print(f"Applying effect: {effect_func.__name__} to segment {i+1}")
                    try:
                        img_movie_clip_affected = effect_func(
                            img_movie_clip_base,
                            duration,
                            target_frame_W,
                            target_frame_H,
                        )
                    except Exception as e_effect:
                        print(
                            f"Error applying effect {effect_func.__name__} to segment {i+1}: {e_effect}"
                        )
                        # Fallback to a default if effect fails
                        img_movie_clip_affected = zoom_in_effect(
                            img_movie_clip_base,
                            duration,
                            target_frame_W,
                            target_frame_H,
                        )
                else:  # Fallback if no effects are defined
                    img_movie_clip_affected = zoom_in_effect(
                        img_movie_clip_base, duration, target_frame_W, target_frame_H
                    )
            else:
                # If no zoom effect, center the base image clip
                # The base image is HxH, frame is WxF (W<H). Centering will crop sides.
                img_movie_clip_affected = img_movie_clip_base.set_position(
                    "center", "center"
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
                        stroke_width=1,
                        method="caption",  # Use caption for auto-sizing to width
                        size=(
                            target_frame_W * 0.9,  # Text width is 90% of frame width
                            None,
                        ),
                        align="center",
                    )
                    .set_position(
                        ("center", 0.8), relative=True
                    )  # Position lower for portrait
                    .set_duration(duration)
                )
                text_segments.append(txt_clip)

            # Composite video for the segment
            video_elements = [
                img_movie_clip_affected
            ] + text_segments  # Use the affected clip
            segment_video_clip = CompositeVideoClip(
                video_elements,
                size=(target_frame_W, target_frame_H),  # Set segment to 9:16
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
