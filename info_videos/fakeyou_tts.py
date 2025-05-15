import os
import requests
import time
import json
import base64
import subprocess
import tempfile

# FakeYou API credentials - should be set as environment variables in production
FAKEYOU_USERNAME = os.getenv("FAKEYOU_USERNAME")
FAKEYOU_PASSWORD = os.getenv("FAKEYOU_PASSWORD")

# Voice token IDs for characters
CHARACTER_VOICE_TOKENS = {
    "peter griffin": "TM:3sk340a43q6n",  # Peter Griffin
    "homer simpson": "TM:c0caxchqrcwc",  # Homer Simpson
}

class FakeYouAPI:
    """
    A client for the FakeYou.com API to generate realistic character TTS
    """
    def __init__(self, username=None, password=None):
        self.base_url = "https://api.fakeyou.com"
        self.username = username or FAKEYOU_USERNAME
        self.password = password or FAKEYOU_PASSWORD
        self.session = requests.Session()
        self.token = None
        self.logged_in = False
    
    def login(self):
        """Log in to FakeYou API and get a session token"""
        if not self.username or not self.password:
            print("Warning: FakeYou credentials not provided. Some features may be limited.")
            return False
        
        login_url = f"{self.base_url}/login"
        login_data = {
            "username_or_email": self.username,
            "password": self.password
        }
        
        try:
            response = self.session.post(login_url, json=login_data)
            response.raise_for_status()
            
            if response.json().get("success"):
                self.logged_in = True
                print("Successfully logged in to FakeYou API")
                return True
            else:
                print(f"Failed to log in: {response.json().get('error_reason')}")
                return False
        except Exception as e:
            print(f"Error logging in to FakeYou API: {e}")
            return False
    
    def generate_tts(self, text, voice_token, output_path=None):
        """
        Generate text-to-speech audio using the specified voice token.
        
        Args:
            text (str): The text to convert to speech
            voice_token (str): The FakeYou voice token ID
            output_path (str): Path to save the audio file (optional)
            
        Returns:
            str: Path to the generated audio file or None if failed
        """
        if not output_path:
            # Create a unique output filename if not provided
            temp_dir = os.path.join(os.getcwd(), "info_videos/assets/audio")
            os.makedirs(temp_dir, exist_ok=True)
            
            safe_text = "".join(c if c.isalnum() else "_" for c in text[:20])
            output_path = os.path.join(temp_dir, f"fakeyou_{safe_text}_{int(time.time())}.mp3")
        
        # Step 1: Request TTS job
        job_url = f"{self.base_url}/tts/inference"
        job_data = {
            "tts_model_token": voice_token,
            "uuid_idempotency_token": base64.b64encode(os.urandom(16)).decode("utf-8"),
            "inference_text": text
        }
        
        try:
            print(f"Requesting FakeYou TTS for text: '{text[:30]}...'")
            response = self.session.post(job_url, json=job_data)
            response.raise_for_status()
            result = response.json()
            
            if not result.get("success"):
                print(f"Failed to request TTS: {result.get('error_reason')}")
                return None
            
            job_token = result.get("inference_job_token")
            print(f"FakeYou TTS job submitted with token: {job_token}")
            
            # Step 2: Poll job status until complete
            status_url = f"{self.base_url}/tts/job/{job_token}"
            max_attempts = 30
            attempts = 0
            
            while attempts < max_attempts:
                time.sleep(2)  # Don't overwhelm the API
                status_response = self.session.get(status_url)
                status_response.raise_for_status()
                status = status_response.json()
                
                state = status.get("state", {}).get("status")
                if state == "complete_success":
                    print("FakeYou TTS generation complete!")
                    break
                elif state in ["complete_failure", "dead"]:
                    print(f"FakeYou TTS generation failed with state: {state}")
                    return None
                
                print(f"FakeYou job status: {state} (attempt {attempts+1}/{max_attempts})")
                attempts += 1
            
            if attempts >= max_attempts:
                print("Timed out waiting for FakeYou TTS completion")
                return None
            
            # Step 3: Download the audio file
            audio_path = status.get("state", {}).get("maybe_public_bucket_wav_audio_path")
            if not audio_path:
                print("No audio path in response")
                return None
            
            audio_url = f"https://storage.googleapis.com/vocodes-public{audio_path}"
            audio_response = requests.get(audio_url)
            audio_response.raise_for_status()
            
            # Save the WAV audio as temporary file
            temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
            with open(temp_wav, "wb") as f:
                f.write(audio_response.content)
            
            # Convert WAV to MP3 using ffmpeg
            try:
                convert_wav_to_mp3(temp_wav, output_path)
                os.remove(temp_wav)  # Clean up temporary WAV file
                print(f"FakeYou audio saved to {output_path}")
                return output_path
            except Exception as e:
                print(f"Error converting audio: {e}")
                # If conversion fails, just rename the WAV file to output path
                os.rename(temp_wav, output_path)
                return output_path
            
        except Exception as e:
            print(f"Error generating TTS with FakeYou API: {e}")
            return None

def convert_wav_to_mp3(wav_file, mp3_file):
    """Convert WAV file to MP3 using ffmpeg"""
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-i", wav_file,
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        mp3_file
    ]
    
    subprocess.run(cmd, check=True)
    
def generate_character_audio(character_name, text, output_path=None):
    """
    Generate audio for a specific character using FakeYou API.
    
    Args:
        character_name (str): Character name (e.g., "peter griffin", "homer simpson")
        text (str): Text to convert to speech
        output_path (str): Path to save the audio file
        
    Returns:
        str: Path to the generated audio file or None if failed
    """
    character_name_lower = character_name.lower()
    voice_token = CHARACTER_VOICE_TOKENS.get(character_name_lower)
    
    if not voice_token:
        print(f"No FakeYou voice token found for character: {character_name}")
        return None
    
    print(f"Using FakeYou API to generate voice for {character_name}")
    api = FakeYouAPI()
    if not api.login():
        print("Using FakeYou API without login")
    
    return api.generate_tts(text, voice_token, output_path)

def is_character_supported(character_name):
    """Check if a character is supported by FakeYou API"""
    return character_name.lower() in CHARACTER_VOICE_TOKENS 