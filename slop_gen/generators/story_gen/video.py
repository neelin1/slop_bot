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


def zoom_in_effect(clip: ImageClip, duration: float) -> ImageClip:
    """Simple zoom in: scales from 100% to 120% over the duration."""
    return clip.resize(lambda t: 1 + 0.2 * (t / duration))


def zoom_out_effect(clip: ImageClip, duration: float) -> ImageClip:
    """Simple zoom out: scales from 120% to 100% over the duration."""
    return clip.resize(lambda t: 1.2 - 0.2 * (t / duration))


def zoom_in_top_right_effect(clip: ImageClip, duration: float) -> ImageClip:
    """Zooms in, keeping the top-right corner of the clip fixed."""
    W, H = clip.w, clip.h
    scale_func = lambda t: 1 + 0.2 * (t / duration)  # Scale from 100% to 120%

    def position_func(t):
        s = scale_func(t)
        # New top-left x: W * (1 - s)
        # New top-left y: 0 (to keep top edge aligned)
        return (W * (1 - s), 0)

    return clip.resize(scale_func).set_position(position_func)


def zoom_out_top_right_effect(clip: ImageClip, duration: float) -> ImageClip:
    """Zooms out, keeping the top-right corner of the clip fixed."""
    W, H = clip.w, clip.h
    # Scale from 120% to 100%
    scale_func = lambda t: 1.2 - 0.2 * (t / duration)

    def position_func(t):
        s = scale_func(t)
        return (W * (1 - s), 0)

    return clip.resize(scale_func).set_position(position_func)


def pan_left_effect(clip: ImageClip, duration: float) -> ImageClip:
    """Pans from right to left."""

    def position_func(t):
        # Start with the right edge of the image at the right edge of the frame
        # End with the left edge of the image at the left edge of the frame
        # This assumes the image is wider than the frame after an initial zoom
        # For simplicity, let's assume a slight zoom to allow panning
        initial_zoom = 1.1  # Ensure image is a bit wider
        img_width_zoomed = clip.w * initial_zoom
        frame_w = clip.w  # Assuming clip.w is the target frame width before this effect

        # Calculate how much the image extends beyond the frame on one side
        overflow_px = (img_width_zoomed - frame_w) / 2

        # Movement range: from +overflow_px (image shifted right) to -overflow_px (image shifted left)
        # We want to pan across this overflow.
        # Let's pan across a portion of the image, say 10% of its original width
        pan_distance = frame_w * 0.10

        # Start position: center the zoomed image, then shift right by pan_distance / 2
        start_x = "center"  # (frame_w - img_width_zoomed) / 2 + pan_distance / 2
        # End position: center the zoomed image, then shift left by pan_distance / 2
        end_x = "center"  # (frame_w - img_width_zoomed) / 2 - pan_distance / 2

        # For moviepy, 'left' or 'right' for x_pos means the edge of the *clip* aligns with frame edge.
        # 'center' is simpler. We need to change the x_pos of the clip.
        # Let the clip be slightly larger
        zoomed_clip = clip.resize(initial_zoom)

        # We want to shift the *content* of the image.
        # If we move the clip's position from 'right' to 'left' over time
        # it means the right edge of the clip moves from frame_right to frame_left

        # Let's try a simpler pan by moving the center
        # Pan from 5% to the right of center to 5% to the left of center
        # This requires the image to be wider than the frame.
        progress = t / duration
        x_position = 0.55 - (
            progress * 0.10
        )  # Center moves from 0.55 (right) to 0.45 (left) relative to frame
        return (x_position, "center")

    # Apply a base zoom to make panning visible if image is same size as frame
    base_zoom_clip = clip.resize(1.2)  # Zoom to 120%
    # To pan left, the content moves left, so the x position of the image moves from right to left
    # We need to ensure the image is wider than the frame for panning to be visible.
    # Let clip.w be frame_width. We resize image to clip.w * 1.2
    # The position of the image's center. (0,0) is top-left of frame.
    # To pan left (content moves from right to left):
    # Start: image is shifted right, so its left edge is at say, 0.1 * frame_width
    # End: image is shifted left, so its right edge is at say, 0.9 * frame_width
    final_width = base_zoom_clip.w

    # This is a simple horizontal pan by changing the 'x_center'
    # The image must be wider than the output for this to work effectively.
    # Position is (x_center, y_center)
    # x_center moves from (frame_width - image_width)/2 + pan_amount to (frame_width - image_width)/2 - pan_amount
    # Let's try a different approach: crop a moving window from a larger image.
    # This is more complex with moviepy's standard effects.
    # A simpler way is to use .set_position with a function of t.
    # Ensure the clip is wider than the frame by zooming it first.
    zoomed_clip = clip.resize(width=clip.w * 1.2)  # Make it 20% wider

    def pos_pan_left(t):
        # Start with image's left edge at frame's left edge. Image is wider.
        # End with image's right edge at frame's right edge.
        # This means the image effectively slides leftwards.
        start_x = 0  # Image's left edge aligns with frame's left edge
        end_x = (
            clip.w - zoomed_clip.w
        )  # Image's left edge is now to the left of frame's left
        # such that image's right edge is at frame's right edge.
        current_x = start_x + (end_x - start_x) * (t / duration)
        return (current_x, "center")

    return zoomed_clip.set_position(pos_pan_left)


def pan_right_effect(clip: ImageClip, duration: float) -> ImageClip:
    """Pans from left to right."""
    zoomed_clip = clip.resize(width=clip.w * 1.2)  # Make it 20% wider

    def pos_pan_right(t):
        start_x = clip.w - zoomed_clip.w
        end_x = 0
        current_x = start_x + (end_x - start_x) * (t / duration)
        return (current_x, "center")

    return zoomed_clip.set_position(pos_pan_right)


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
available_effects: List[Callable[[ImageClip, float], ImageClip]] = [
    zoom_in_effect,
    zoom_out_effect,
    zoom_in_top_right_effect,
    zoom_out_top_right_effect,
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
                # img_movie_clip = img_movie_clip.resize(
                #     lambda t: 1 + 0.2 * (t / duration)
                # )
                if available_effects:
                    effect_func = random.choice(available_effects)
                    print(f"Applying effect: {effect_func.__name__} to segment {i+1}")
                    try:
                        img_movie_clip = effect_func(img_movie_clip, duration)
                    except Exception as e_effect:
                        print(
                            f"Error applying effect {effect_func.__name__} to segment {i+1}: {e_effect}"
                        )
                        # Fallback to a default if effect fails, e.g., simple zoom or no zoom
                        img_movie_clip = zoom_in_effect(
                            img_movie_clip, duration
                        )  # Fallback
                else:  # Fallback if no effects are defined (e.g. zoom_effect is True but list is empty)
                    img_movie_clip = zoom_in_effect(img_movie_clip, duration)

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
