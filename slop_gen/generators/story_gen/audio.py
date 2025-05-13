import os
import io
import subprocess
from typing import List, Dict, Optional  # Added Dict, Optional
from slop_gen.utils.api_utils import text_to_speech


def change_speed_ffmpeg(
    audio_bytes: bytes, speed: float, in_fmt: str, out_fmt: str
) -> bytes:
    """
    Uses ffmpeg -filter:a atempo to change speed.
    speed <1.0 -> slower, >1.0 -> faster.
    """
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        in_fmt,
        "-i",
        "pipe:0",
        "-filter:a",
        f"atempo={speed}",
        "-f",
        out_fmt,
        "pipe:1",
    ]
    proc = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, err = proc.communicate(audio_bytes)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {err.decode().strip()}")
    return out


def generate_audio_for_scenes(
    scene_descriptions: List[Dict],  # Changed from lines: list[str]
    output_dir: str = "assets/generated_audio",  # Changed default dir
    model: str = "openai.tts-hd",
    voice: str = "alloy",
    speed: float = 1.0,  # <1.0 = slower
) -> List[Optional[str]]:  # Changed to List[Optional[str]]
    os.makedirs(output_dir, exist_ok=True)
    paths: List[Optional[str]] = []  # Changed to List[Optional[str]]

    for idx, scene in enumerate(scene_descriptions):
        line = scene.get("text")
        if not line or line == "@@@":  # Handle empty text or silent scene marker
            if line == "@@@":
                print(
                    f"ℹ️ Scene {idx+1} is marked as silent (@@@). No audio will be generated."
                )
            else:
                print(f"⚠️ Scene {idx+1} has no text. Skipping audio generation.")
            paths.append(None)
            continue
        try:
            # 1) Synthesize as MP3
            raw_bytes = text_to_speech(text=line, model=model, voice=voice, fmt="mp3")
            # 2) Slow it down (if speed is not 1.0)
            if speed != 1.0:
                raw_bytes = change_speed_ffmpeg(
                    raw_bytes, speed, in_fmt="mp3", out_fmt="mp3"
                )
            # 3) Write out
            out_path = os.path.join(
                output_dir, f"scene_audio_{idx}.mp3"
            )  # Changed naming to scene_audio_idx
            with open(out_path, "wb") as f:
                f.write(raw_bytes)
            paths.append(out_path)
            print(f"✅ Generated audio for scene {idx+1}: {out_path}")

        except Exception as e:
            print(
                f"❌ Failed to generate audio for scene {idx+1} (text: '{line[:50]}...'): {e}"
            )
            paths.append(None)  # This is now type-correct

    return paths
