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
import moviepy.audio.fx.all as afx

from slop_gen.generators.story_gen.planning import PostProcessing

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
# Max vertical offset fraction to ensure content covers frame during zoom (with S_BASE minimum zoom)
# This is used to calculate content_offset_y. An image of height H, scaled by S_BASE,
# will have scaled height S_BASE*H. The frame height is H (or rather, img_H is target_frame_H).
# The visible portion of the scaled image is H. Extra scaled image part is (S_BASE*H - H).
# This extra part is distributed above and below, so (S_BASE*H - H)/2 is max shift from center.
# offset_y is in original image coords of the base clip (which is HxH). Scaled offset is S_BASE*offset_y.
# So, S_BASE*offset_y <= (S_BASE*H - H)/2.
# This means offset_y <= H * (S_BASE - 1) / (2 * S_BASE).
# The fraction of H is (S_BASE - 1) / (2 * S_BASE).
MAX_VERTICAL_OFFSET_FRACTION_FOR_ZOOM = (S_BASE - 1) / (2 * S_BASE)  # Approx 0.0833


def zoom_in_effect(
    clip: ImageClip,
    duration: float,
    frame_W: int,
    frame_H: int,
    img_W: int,
    img_H: int,
    offset_x: float,
    offset_y: float,
) -> ImageClip:
    """Zooms in, keeping an initially offset center point of the content centered in the frame."""
    scale_func = lambda t: S_BASE + S_DELTA * (t / duration)

    def pos_func(t):
        s = scale_func(t)
        # Target content point (img_W/2 + offset_x, img_H/2 + offset_y) should be at frame center (frame_W/2, frame_H/2)
        clip_x = frame_W / 2 - s * (img_W / 2 + offset_x)
        clip_y = frame_H / 2 - s * (img_H / 2 + offset_y)
        return (clip_x, clip_y)

    return clip.resize(scale_func).set_position(pos_func)  # type: ignore


def zoom_out_effect(
    clip: ImageClip,
    duration: float,
    frame_W: int,
    frame_H: int,
    img_W: int,
    img_H: int,
    offset_x: float,
    offset_y: float,
) -> ImageClip:
    """Zooms out, keeping an initially offset center point of the content centered in the frame."""
    scale_func = lambda t: (S_BASE + S_DELTA) - S_DELTA * (t / duration)

    def pos_func(t):
        s = scale_func(t)
        clip_x = frame_W / 2 - s * (img_W / 2 + offset_x)
        clip_y = frame_H / 2 - s * (img_H / 2 + offset_y)
        return (clip_x, clip_y)

    return clip.resize(scale_func).set_position(pos_func)  # type: ignore


def zoom_in_top_right_effect(
    clip: ImageClip,
    duration: float,
    frame_W: int,
    frame_H: int,
    img_W: int,
    img_H: int,
    offset_x: float,
    offset_y: float,
) -> ImageClip:
    """Zooms in, keeping an initially offset top-right point of the content fixed to frame's top-right."""
    scale_func = lambda t: S_BASE + S_DELTA * (t / duration)

    def pos_func(t):
        s = scale_func(t)
        # Target content point (img_W + offset_x, 0 + offset_y) relative to image TL
        # should be at frame's top-right (frame_W, 0)
        clip_x = frame_W - s * (img_W + offset_x)
        clip_y = 0 - s * (0 + offset_y)  # offset_y is from top-left of image
        return (clip_x, clip_y)

    return clip.resize(scale_func).set_position(pos_func)  # type: ignore


def zoom_out_top_right_effect(
    clip: ImageClip,
    duration: float,
    frame_W: int,
    frame_H: int,
    img_W: int,
    img_H: int,
    offset_x: float,
    offset_y: float,
) -> ImageClip:
    """Zooms out, keeping an initially offset top-right point of the content fixed to frame's top-right."""
    scale_func = lambda t: (S_BASE + S_DELTA) - S_DELTA * (t / duration)

    def pos_func(t):
        s = scale_func(t)
        clip_x = frame_W - s * (img_W + offset_x)
        clip_y = 0 - s * (0 + offset_y)
        return (clip_x, clip_y)

    return clip.resize(scale_func).set_position(pos_func)  # type: ignore


# Pan effects would also need to accept img_W, img_H, offset_x, offset_y and be adjusted
def pan_left_to_right_effect(
    clip: ImageClip,
    duration: float,
    frame_W: int,
    frame_H: int,
    img_W_clip: int,
    img_H_clip: int,
    offset_x_ignored: float,
    offset_y: float,
) -> ImageClip:
    """Pans content from left to right, with no zoom. Uses base clip scaled to frame height."""
    # clip is img_movie_clip_base, so img_W_clip == img_H_clip == frame_H in current setup
    # Vertical position based on offset_y (content point img_H_clip/2 + offset_y should be at frame_H/2)
    # Since img_H_clip == frame_H, y_pos_for_clip = -offset_y
    y_pos = (
        0.0  # NEW: Ensure the HxH clip is vertically centered in the H-height frame.
    )

    def pos_func(t):
        # Horizontal pan: clip's left edge moves from 0 to (frame_W - img_W_clip)
        x_start_clip = 0
        x_end_clip = frame_W - img_W_clip
        current_x_clip = x_start_clip + (x_end_clip - x_start_clip) * (t / duration)
        return (current_x_clip, y_pos)

    # No resize, uses the clip as is (which should be img_movie_clip_base)
    return clip.set_position(pos_func)


def pan_right_to_left_effect(
    clip: ImageClip,
    duration: float,
    frame_W: int,
    frame_H: int,
    img_W_clip: int,
    img_H_clip: int,
    offset_x_ignored: float,
    offset_y: float,
) -> ImageClip:
    """Pans content from right to left, with no zoom. Uses base clip scaled to frame height."""
    y_pos = 0.0  # NEW: Ensure the HxH clip is vertically centered.

    def pos_func(t):
        # Horizontal pan: clip's left edge moves from (frame_W - img_W_clip) to 0
        x_start_clip = frame_W - img_W_clip
        x_end_clip = 0
        current_x_clip = x_start_clip + (x_end_clip - x_start_clip) * (t / duration)
        return (current_x_clip, y_pos)

    return clip.set_position(pos_func)


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
available_effects: List[
    Callable[[ImageClip, float, int, int, int, int, float, float], ImageClip]
] = [
    zoom_in_effect,
    zoom_out_effect,
    zoom_in_top_right_effect,
    zoom_out_top_right_effect,
    pan_left_to_right_effect,
    pan_right_to_left_effect,
]


def create_video_from_assets(
    image_paths: List[str],
    audio_paths: List[Optional[str]],
    scene_texts: List[str],
    output_path: str = "assets/output/story_video.mp4",
    fps: int = 24,
    height: int = 1080,  # Defaulted to a common portrait height for social media
    music_path: Optional[str] = None,
    music_volume_param: Optional[float] = None,
    wrap_width: int = 30,  # Adjusted for portrait, might need tuning
    zoom_effect: bool = True,  # Added to control the zoom
    default_segment_duration: float = 3.0,  # Duration for segments with no audio
    post_processing_effects: Optional[
        List[PostProcessing]
    ] = None,  # Added for captions control
) -> None:
    clips = []
    total_segments = len(image_paths)

    # Determine actual music volume to use
    actual_music_volume = 0.3  # Default if not overridden
    if music_volume_param is not None:
        try:
            # The user wants 1.0 to be the current setting, which is 0.3
            # So, we scale the input relative to this baseline.
            # If user provides 1.0, actual_music_volume remains 0.3.
            # If user provides 0.5, actual_music_volume becomes 0.3 * 0.5 = 0.15
            # If user provides 2.0, actual_music_volume becomes 0.3 * 2.0 = 0.6
            actual_music_volume = 0.3 * float(music_volume_param)
        except ValueError:
            print(
                f"Warning: Invalid music_volume_param '{music_volume_param}'. Using default volume {actual_music_volume}."
            )

    # Calculate target 9:16 frame dimensions
    target_frame_H = height
    target_frame_W = int(round(target_frame_H * 9 / 16))
    if target_frame_W % 2 != 0:  # Ensure width is even for some codecs
        target_frame_W += 1

    print(f"Target video resolution: {target_frame_W}x{target_frame_H} (9:16)")

    # Random factor for initial view offset (percentage of max pannable area)
    RANDOM_HORIZONTAL_OFFSET_FACTOR = (
        0.4  # For zoom effects, fraction of pannable width
    )
    # RANDOM_VERTICAL_OFFSET_FRACTION = 0.1  # For all effects, fraction of image height # REMOVED - Using new global constant

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

    last_applied_effect_name: Optional[str] = None  # Track the last applied effect
    pan_effect_names = {
        "pan_left_to_right_effect",
        "pan_right_to_left_effect",
    }  # Define pan effect names

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

            # Get dimensions of the base image clip (which is square target_frame_H x target_frame_H)
            img_W, img_H = img_movie_clip_base.w, img_movie_clip_base.h

            # Calculate random initial content offsets for this segment
            # Max pannable content area at S_BASE zoom relative to frame (for X offset of zoom effects)
            # Ensure these are non-negative if S_BASE makes image smaller than frame (should not happen with S_BASE > 1)
            max_content_pan_x_for_zoom = max(0, (S_BASE * img_W - target_frame_W) / 2)
            content_offset_x = (
                random.uniform(
                    -RANDOM_HORIZONTAL_OFFSET_FACTOR, RANDOM_HORIZONTAL_OFFSET_FACTOR
                )
                * max_content_pan_x_for_zoom
            )

            # Vertical offset based on a fraction of image height (for all effects)
            # img_H here is the height of img_movie_clip_base (which is target_frame_H)
            max_abs_vertical_offset = (
                img_H * MAX_VERTICAL_OFFSET_FRACTION_FOR_ZOOM
            )  # Use the new constant
            content_offset_y = random.uniform(
                -max_abs_vertical_offset, max_abs_vertical_offset
            )

            current_effect_name_for_update: Optional[str] = (
                None  # Stores name of effect applied in this iteration
            )

            if zoom_effect:
                if available_effects:
                    effect_func_to_apply: Optional[Callable[..., ImageClip]] = None

                    eligible_choices = list(available_effects)  # Start with all effects

                    if (
                        last_applied_effect_name
                        and last_applied_effect_name in pan_effect_names
                    ):
                        # If last effect was a pan, try to pick a different one
                        filtered_choices = [
                            eff
                            for eff in eligible_choices
                            if eff.__name__ != last_applied_effect_name
                        ]
                        if filtered_choices:
                            effect_func_to_apply = random.choice(filtered_choices)
                        else:
                            # Fallback: if filtering left no choices (e.g., only one effect type, and it was the last pan)
                            effect_func_to_apply = random.choice(
                                eligible_choices
                            )  # Pick from original list
                    else:
                        # Last effect was not a pan, or no last effect yet, so pick any.
                        effect_func_to_apply = random.choice(eligible_choices)

                    if effect_func_to_apply:
                        print(
                            f"Applying effect: {effect_func_to_apply.__name__} to segment {i+1} with offset ({content_offset_x:.2f}, {content_offset_y:.2f})"
                        )
                        try:
                            img_movie_clip_affected = effect_func_to_apply(
                                img_movie_clip_base,
                                duration,
                                target_frame_W,
                                target_frame_H,
                                img_W,
                                img_H,
                                content_offset_x,
                                content_offset_y,
                            )
                            current_effect_name_for_update = (
                                effect_func_to_apply.__name__
                            )
                        except Exception as e_effect:
                            print(
                                f"Error applying effect {effect_func_to_apply.__name__} to segment {i+1}: {e_effect}"
                            )
                            # Fallback to a default if effect fails
                            img_movie_clip_affected = zoom_in_effect(
                                img_movie_clip_base,
                                duration,
                                target_frame_W,
                                target_frame_H,
                                img_W,
                                img_H,
                                0,
                                0,  # No offset for fallback
                            )
                            current_effect_name_for_update = zoom_in_effect.__name__
                    else:  # Should not happen if available_effects is not empty
                        print(
                            f"Warning: No effect function was selected for segment {i+1}. Using default zoom_in_effect."
                        )
                        img_movie_clip_affected = zoom_in_effect(
                            img_movie_clip_base,
                            duration,
                            target_frame_W,
                            target_frame_H,
                            img_W,
                            img_H,
                            0,
                            0,
                        )
                        current_effect_name_for_update = zoom_in_effect.__name__

                else:  # Fallback if no effects are defined in available_effects list
                    print(
                        f"No effects in available_effects list. Using default zoom_in_effect for segment {i+1}."
                    )
                    img_movie_clip_affected = zoom_in_effect(
                        img_movie_clip_base,
                        duration,
                        target_frame_W,
                        target_frame_H,
                        img_W,
                        img_H,
                        0,
                        0,  # No offset for fallback
                    )
                    current_effect_name_for_update = zoom_in_effect.__name__
            else:
                # If no zoom effect, center the base image clip considering the random offset
                # The base image is HxH, frame is WxH (W<H).
                # We need to position it so the (img_center + offset) is at frame_center at S_BASE scale.
                # Clip position for a static view at S_BASE scale with offset:
                s_static = S_BASE  # or 1.0 if no zoom effect means no initial zoom beyond fitting
                clip_x_static = target_frame_W / 2 - s_static * (
                    img_W / 2 + content_offset_x
                )
                clip_y_static = target_frame_H / 2 - s_static * (
                    img_H / 2 + content_offset_y
                )
                img_movie_clip_affected = img_movie_clip_base.resize(
                    s_static
                ).set_position((clip_x_static, clip_y_static))
                current_effect_name_for_update = (
                    None  # No specific 'effect' from the list was chosen
                )

            last_applied_effect_name = (
                current_effect_name_for_update  # Update for the next iteration
            )

            # Text Clip
            text_segments = []
            if (
                raw_text
                and raw_text != "@@@"
                and post_processing_effects
                and PostProcessing.CAPTION in post_processing_effects
            ):  # Don't add text for silent scenes or if text is empty, and check for CAPTION post-processing
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
                bg_music_clip = afx.loop(  # type: ignore
                    full_music_clip, duration=final_video_clip.duration
                ).volumex(actual_music_volume)
            else:
                # Try to pick a somewhat random segment if music is longer
                max_start_time = max(
                    0, full_music_clip.duration - final_video_clip.duration
                )
                start_time = random.uniform(0, max_start_time)
                bg_music_clip = full_music_clip.subclip(
                    start_time, start_time + final_video_clip.duration
                ).volumex(actual_music_volume)

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
