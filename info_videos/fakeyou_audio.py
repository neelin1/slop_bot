import requests
import uuid
import time
import os

# Dictionary mapping character names to FakeYou voice tokens
CHARACTER_VOICES = {
    "Peter Griffin": "weight_883h5cw4q48cpsmjvjypxs0dc",  # Peter Griffin
    "Homer Simpson": "weight_xcgb5zyhewq39gkgq7qcjpw8v"   # Homer Simpson
}

# Using the same credentials as in fakeyou.py
USERNAME = "abc123123123@gmail.com"
PASSWORD = "aaaaaa"

def generate_fakeyou_audio(text, output_file, character_name):
    """
    Generate audio using FakeYou.com API for specific characters.
    
    Args:
        text (str): Text to convert to speech
        output_file (str): Path to save the audio file
        character_name (str): Name of the character to use (must be in CHARACTER_VOICES)
        
    Returns:
        str: Path to the generated audio file or None if failed
    """
    # Check if character is supported
    voice_token = CHARACTER_VOICES.get(character_name)
    if not voice_token:
        print(f"❌ Character '{character_name}' is not supported by FakeYou integration.")
        return None
    
    # Create directory for output file if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # === LOGIN ===
    session = requests.Session()
    credentials = {
        "username_or_email": USERNAME,
        "password": PASSWORD
    }

    print(f"  Logging in to FakeYou for {character_name} voice...")
    login_response = session.post("https://api.fakeyou.com/v1/login", json=credentials)

    if login_response.status_code != 200:
        print(f"❌ FakeYou login failed: {login_response.text}")
        return None
    
    # Add delay after login to avoid rate limiting
    print(f"  Pausing for 3 seconds to avoid rate limiting...")
    time.sleep(3)
    
    # === SUBMIT TTS JOB ===
    job_payload = {
        "tts_model_token": voice_token,
        "uuid_idempotency_token": str(uuid.uuid4()),
        "inference_text": text
    }

    print(f"  Submitting TTS job for {character_name}...")
    job_response = session.post("https://api.fakeyou.com/tts/inference", json=job_payload)

    if job_response.status_code != 200:
        print(f"❌ Failed to start FakeYou TTS job: {job_response.text}")
        return None

    inference_job_token = job_response.json().get("inference_job_token")
    print(f"  FakeYou job submitted: {inference_job_token}")
    
    # Add delay after job submission to avoid rate limiting
    print(f"  Pausing for 3 seconds to avoid rate limiting...")
    time.sleep(3)

    # === POLL FOR COMPLETION ===
    poll_url = f"https://api.fakeyou.com/tts/job/{inference_job_token}"
    audio_path = None

    print(f"  Waiting for FakeYou job to complete...")
    for attempt in range(60):  # Poll for up to 60 seconds
        time.sleep(1)
        response = session.get(poll_url)

        if response.status_code != 200:
            print(f"❌ FakeYou poll error: HTTP {response.status_code}")
            print(response.text)
            break

        try:
            data = response.json()
        except Exception:
            print("❌ Failed to parse JSON from FakeYou response")
            break

        job_status = data.get('state', {}).get('status')
        audio_path = data.get('state', {}).get('maybe_public_bucket_wav_audio_path')

        if job_status == 'complete_success' and audio_path:
            break
        elif job_status in ['dead', 'attempt_failed']:
            print(f"❌ FakeYou job failed with status: {job_status}")
            return None

    if not audio_path:
        print("❌ FakeYou job completed but no audio path found.")
        return None

    # === DOWNLOAD THE AUDIO FILE (Try Both CDNs) ===
    audio_url_primary = f"https://cdn.fakeyou.com{audio_path}"
    audio_url_fallback = f"https://cdn-2.fakeyou.com{audio_path}"

    print(f"  Downloading audio from: {audio_url_primary}")
    audio_response = session.get(audio_url_primary)

    if audio_response.status_code != 200:
        print(f"  Failed on primary CDN (HTTP {audio_response.status_code}), trying fallback...")
        audio_response = session.get(audio_url_fallback)
        audio_url = audio_url_fallback
    else:
        audio_url = audio_url_primary

    # Save the file if download worked
    if audio_response.status_code == 200:
        with open(output_file, "wb") as f:
            f.write(audio_response.content)
        print(f"✅ {character_name} audio saved as '{output_file}'")
        
        # Add delay after successful download to avoid rate limiting for next call
        print(f"  Pausing for 3 seconds to avoid rate limiting for next request...")
        time.sleep(3)
        
        return output_file
    else:
        print(f"❌ Failed to download audio from both FakeYou CDNs (HTTP {audio_response.status_code})")
        return None 