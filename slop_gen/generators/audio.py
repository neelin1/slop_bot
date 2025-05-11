import os
from slop_gen.utils.api_utils import text_to_speech

def generate_audio(
    lines: list[str],
    output_dir: str = "assets/audio",
    model: str = "openai.tts-hd",
    voice: str = "alloy",
    fmt: str = "wav"
) -> list[str]:
    """
    For each line in `lines`, synthesize speech and save to disk.
    Returns a list of file paths (or None on failure).
    """
    os.makedirs(output_dir, exist_ok=True)
    paths: list[str] = []

    for idx, line in enumerate(lines):
        try:
            audio_bytes = text_to_speech(text=line, model=model, voice=voice, fmt=fmt)
            file_path = os.path.join(output_dir, f"audio_{idx+1}.{fmt}")
            with open(file_path, "wb") as f:
                f.write(audio_bytes)
            paths.append(file_path)
        except Exception as e:
            print(f"❌ Failed to generate audio for line {idx+1}: {e}")
            paths.append(None)

    return paths
