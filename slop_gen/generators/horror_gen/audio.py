import os
import io
import subprocess
from slop_gen.utils.api_utils import text_to_speech

def change_speed_ffmpeg(audio_bytes: bytes, speed: float, in_fmt: str, out_fmt: str) -> bytes:
    """
    Uses ffmpeg -filter:a atempo to change speed.
    speed <1.0 -> slower, >1.0 -> faster.
    """
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-f", in_fmt,
        "-i", "pipe:0",
        "-filter:a", f"atempo={speed}",
        "-f", out_fmt,
        "pipe:1",
    ]
    proc = subprocess.Popen(cmd,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate(audio_bytes)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {err.decode().strip()}")
    return out

def generate_audio(
    lines: list[str],
    output_dir: str = "assets/audio",
    model: str = "openai.tts-hd",
    voice: str = "alloy",
    speed: float = 1.0,     # <1.0 = slower
) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    paths: list[str] = []

    for idx, line in enumerate(lines):
        try:
            # 1) Synthesize as MP3
            raw_bytes = text_to_speech(text=line, model=model, voice=voice, fmt="mp3")
            # 2) Slow it down
            if speed != 1.0:
                raw_bytes = change_speed_ffmpeg(raw_bytes, speed, in_fmt="mp3", out_fmt="mp3")
            # 3) Write out
            out_path = os.path.join(output_dir, f"audio_{idx+1}.mp3")
            with open(out_path, "wb") as f:
                f.write(raw_bytes)
            paths.append(out_path)

        except Exception as e:
            print(f"❌ Failed to generate audio for line {idx+1}: {e}")
            paths.append(None)

    return paths
