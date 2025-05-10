import os
import requests
from time import sleep

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

def generate_audio(lines, output_dir="assets/audio", voice_id=VOICE_ID):
    """
    Generate narration audio for each line using ElevenLabs TTS.

    Args:
        lines (list[str]): Text lines to convert to speech.
        output_dir (str): Directory to save MP3 files (default: assets/audio).
        voice_id (str): ElevenLabs voice ID.

    Returns:
        list[str]: List of MP3 file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    audio_paths = []

    for i, line in enumerate(lines):
        data = {
            "text": line,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
        }

        try:
            response = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers=headers,
                json=data
            )
            if response.status_code == 200:
                audio_path = os.path.join(output_dir, f"line_{i+1}.mp3")
                with open(audio_path, "wb") as f:
                    f.write(response.content)
                audio_paths.append(audio_path)
            else:
                print(f"⚠️ Failed audio gen for line {i+1}: {response.text}")
                audio_paths.append(None)
        except Exception as e:
            print(f"❌ Error during audio gen for line {i+1}: {e}")
            audio_paths.append(None)

        sleep(1)

    return audio_paths
