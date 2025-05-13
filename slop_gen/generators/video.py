import os
import random
import textwrap
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    CompositeAudioClip,
)
from moviepy.video.fx import crop, resize  
from moviepy.config import change_settings
change_settings({ "IMAGEMAGICK_BINARY": "magick" })

def pan_effect(clip, style, duration):
    if style == "zoom_in":
        return clip.resize(lambda t: 1 + 0.05 * t)  # more subtle zoom
    elif style == "zoom_out":
        return clip.resize(lambda t: 1.05 - 0.05 * t)
    elif style == "pan_left":
        max_pan = 30  # pixels
        return clip.set_position(lambda t: (int(max_pan * (t / duration)), "center"))
    elif style == "pan_right":
        max_pan = 30  # pixels
        return clip.set_position(lambda t: (int(-max_pan * (t / duration)), "center"))
    else:
        return clip

def create_video(
    image_paths: list[str],
    audio_paths: list[str],
    output_path: str = "assets/output/final_horror_clip_2.mp4",
    story_lines: list[str] | None = None,
    fps: int = 24,
    height: int = 720,
    music_path: str | None = None,
    music_volume: float = 0.4,
    wrap_width: int = 40
) -> None:
    clips = []

    for i, (img_path, audio_path) in enumerate(zip(image_paths, audio_paths)):
        if not img_path or not audio_path:
            print(f"⚠️ Skipping segment {i+1} – missing image or audio.")
            continue

        try:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration

            style = random.choice(["zoom_in", "zoom_out", "pan_left", "pan_right", "none"])
            print(f"🎞️ Segment {i+1}: Applying style → {style}")

            base_clip = (
                ImageClip(img_path)
                .set_duration(duration)
                .resize(height=height)
            )

            img_clip = pan_effect(base_clip, style, duration)

            raw_text = story_lines[i] if story_lines and i < len(story_lines) else ""
            wrapped = textwrap.fill(raw_text, width=wrap_width)

            txt_clip = (
                TextClip(
                    wrapped,
                    fontsize=30,
                    font="Arial-Bold",
                    color="white",
                    stroke_color="white",
                    stroke_width=2,
                    method="label"
                )
                .set_position(("center", 0.5), relative=True)
                .set_duration(duration)
            )

            segment = CompositeVideoClip([img_clip, txt_clip]).set_audio(audio_clip)
            clips.append(segment)

        except Exception as e:
            print(f"❌ Error building segment {i+1}: {e}")

    if not clips:
        print("❌ No segments to concatenate. Aborting.")
        return

    final = concatenate_videoclips(clips, method="compose")

    if music_path and os.path.exists(music_path):
        full_music = AudioFileClip(music_path)
        max_start = max(0, full_music.duration - final.duration)
        start_time = random.uniform(0, max_start)
        bg_slice = (
            full_music
            .subclip(start_time, start_time + final.duration)
            .volumex(music_volume)
        )
        final = final.set_audio(CompositeAudioClip([final.audio, bg_slice]))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final.write_videofile(output_path, fps=fps)
    print(f"✅ Video written to {output_path}")
