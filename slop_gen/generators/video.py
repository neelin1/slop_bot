import os
from moviepy import (
    ImageClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
)


def create_video(image_paths, audio_paths, output_path="assets/output/final_horror_clip.mp4", story_lines=None):
    """
    Combines images, narration, and centered text into a video.

    Args:
        image_paths (list[str]): List of image file paths.
        audio_paths (list[str]): List of audio file paths.
        output_path (str): Output video path.
        story_lines (list[str], optional): Lines of text to overlay on the images.
    """
    clips = []

    for i, (img, audio) in enumerate(zip(image_paths, audio_paths)):
        if img is None or audio is None:
            print(f"⚠️ Skipping frame {i+1} due to missing assets.")
            continue

        try:
            audio_clip = AudioFileClip(audio)
            duration = audio_clip.duration

            # Load image and scale
            image_clip = ImageClip(img).set_duration(duration).resize(height=720)

            # Create centered text overlay
            line = story_lines[i] if story_lines and i < len(story_lines) else ""
            text_clip = (
                TextClip(line, fontsize=40, color="white", font="Arial-Bold")
                .set_position("center")
                .set_duration(duration)
                .margin(top=20, bottom=20, opacity=0)  # Padding
                .with_stroke(color="black", width=2)  # Improve contrast
            )

            # Composite: image + text + audio
            video_clip = CompositeVideoClip([image_clip, text_clip]).set_audio(audio_clip)

            clips.append(video_clip)

        except Exception as e:
            print(f"❌ Failed to process clip {i+1}: {e}")

    if clips:
        final_video = concatenate_videoclips(clips, method="compose")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        final_video.write_videofile(output_path, fps=24)
    else:
        print("❌ No clips to compile into video.")
