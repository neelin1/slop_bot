import os

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
)

def create_video(
    image_paths: list[str],
    audio_paths: list[str],
    output_path: str = "assets/output/final_horror_clip.mp4",
    story_lines: list[str] | None = None,
    fps: int = 24,
    height: int = 720
) -> None:
    """
    Combines images, narration audio, and overlaid text into a single video,
    with a subtle zoom-in effect and very small, centered captions.
    """
    clips = []

    for i, (img_path, audio_path) in enumerate(zip(image_paths, audio_paths)):
        if not img_path or not audio_path:
            print(f"⚠️ Skipping segment {i+1} – missing image or audio.")
            continue

        try:
            # load audio and get its duration
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration

            # load & resize image, then apply a zoom-in from 100% → 120%
            img_clip = (
                ImageClip(img_path)
                .set_duration(duration)
                .resize(height=height)
                .resize(lambda t: 1 + 0.2 * (t / duration))
            )

            # prepare even smaller, centered text overlay
            text = (story_lines[i] if story_lines and i < len(story_lines) else "")
            txt_clip = (
                TextClip(
                    text,
                    fontsize=14,                     # very small text
                    font="Arial-Bold",
                    color="white",
                    stroke_color="black",
                    stroke_width=1,
                    method="label"
                )
                .set_position(("center", "center"))
                .set_duration(duration)
            )

            # composite image + text + audio
            segment = CompositeVideoClip([img_clip, txt_clip]).set_audio(audio_clip)
            clips.append(segment)

        except Exception as e:
            print(f"❌ Error building segment {i+1}: {e}")

    if not clips:
        print("❌ No segments to concatenate. Aborting.")
        return

    # concatenate and write final video
    final = concatenate_videoclips(clips, method="compose")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final.write_videofile(output_path, fps=fps)
    print(f"✅ Video written to {output_path}")
