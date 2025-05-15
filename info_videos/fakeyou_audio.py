import requests
import uuid
import time
import os
import random

# Dictionary mapping character names to FakeYou voice tokens
CHARACTER_VOICES = {
    "Peter Griffin": "weight_883h5cw4q48cpsmjvjypxs0dc",  # Peter Griffin
    "Peter": "weight_883h5cw4q48cpsmjvjypxs0dc",  # Alternate key for Peter Griffin
    
    "Homer Simpson": "weight_qnn4ns4r2a8x5abgb6fdg7tyz",  # Homer Simpson
    "Homer": "weight_qnn4ns4r2a8x5abgb6fdg7tyz",  # Alternate key for Homer Simpson
    
    "Eric Cartman": "weight_h8ebh6fyjyrr1vsjregw6yz8y",   # Eric Cartman
    "Eric": "weight_h8ebh6fyjyrr1vsjregw6yz8y",   # Alternate key for Eric Cartman
    
    "Stewie Griffin": "weight_c8nd3fvvk92xmafpd5anbyb9a",  # Stewie Griffin
    "Stewie": "weight_c8nd3fvvk92xmafpd5anbyb9a",  # Alternate key for Stewie Griffin
    
    "Mickey Mouse": "weight_hq8xbqzx28w21fmx76tqsdbnd",  # Mickey Mouse
    "Mickey": "weight_hq8xbqzx28w21fmx76tqsdbnd"  # Alternate key for Mickey Mouse
}

# Using the same credentials as in fakeyou.py
USERNAME = "abc123123123@gmail.com"
PASSWORD = "aaaaaa"

def generate_fakeyou_audio(text, output_file, character_name, max_retries=3):
    """
    Generate audio using FakeYou.com API for specific characters.
    
    Args:
        text (str): Text to convert to speech
        output_file (str): Path to save the audio file
        character_name (str): Name of the character to use (must be in CHARACTER_VOICES)
        max_retries (int): Maximum number of retry attempts for failed operations
        
    Returns:
        str: Path to the generated audio file or None if failed
    """
    for retry_count in range(max_retries + 1):  # +1 to include the initial attempt
        if retry_count > 0:
            # Only print retry message if this is a retry attempt
            backoff_time = 5 + random.randint(1, 5) * retry_count  # Exponential backoff with randomization
            print(f" Retry attempt {retry_count}/{max_retries} for {character_name} after {backoff_time} seconds...")
            time.sleep(backoff_time)  # Exponential backoff
        
        # Check if character is supported
        voice_token = CHARACTER_VOICES.get(character_name)
        if not voice_token:
            print(f"Character '{character_name}' is not supported by FakeYou integration.")
            return None
        
        print(f" Using FakeYou voice token: {voice_token} for {character_name}")
        
        # Create directory for output file if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # === LOGIN ===
        session = requests.Session()
        credentials = {
            "username_or_email": USERNAME,
            "password": PASSWORD
        }

        print(f"  Logging in to FakeYou for {character_name} voice...")
        try:
            login_response = session.post("https://api.fakeyou.com/v1/login", json=credentials)

            if login_response.status_code != 200:
                print(f"FakeYou login failed: {login_response.text}")
                continue  # Try again if we have retries left
            
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
                print(f"Failed to start FakeYou TTS job: {job_response.text}")
                continue  # Try again if we have retries left

            inference_job_token = job_response.json().get("inference_job_token")
            print(f"  FakeYou job submitted: {inference_job_token}")
            
            # Add delay after job submission to avoid rate limiting
            print(f"  Pausing for 3 seconds to avoid rate limiting...")
            time.sleep(3)

            # === POLL FOR COMPLETION ===
            poll_url = f"https://api.fakeyou.com/tts/job/{inference_job_token}"
            audio_path = None

            print(f"  Waiting for FakeYou job to complete...")
            job_success = False
            
            for attempt in range(60):  # Poll for up to 60 seconds
                time.sleep(1)
                response = session.get(poll_url)

                if response.status_code != 200:
                    print(f"FakeYou poll error: HTTP {response.status_code}")
                    print(response.text)
                    break

                try:
                    data = response.json()
                except Exception:
                    print(" Failed to parse JSON from FakeYou response")
                    break

                job_status = data.get('state', {}).get('status')
                audio_path = data.get('state', {}).get('maybe_public_bucket_wav_audio_path')

                if job_status == 'complete_success' and audio_path:
                    job_success = True
                    break
                elif job_status in ['dead', 'attempt_failed']:
                    print(f" FakeYou job failed with status: {job_status}")
                    break

            if not job_success or not audio_path:
                print(" FakeYou job completed but no audio path found.")
                continue  # Try again if we have retries left

            # === DOWNLOAD THE AUDIO FILE (Try Both CDNs) ===
            audio_url_primary = f"https://cdn.fakeyou.com{audio_path}"
            audio_url_fallback = f"https://cdn-2.fakeyou.com{audio_path}"
            download_success = False

            print(f"  Downloading audio from: {audio_url_primary}")
            try:
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
                    
                    download_success = True
                    return output_file
                else:
                    print(f"Failed to download audio from both FakeYou CDNs (HTTP {audio_response.status_code})")
            except Exception as e:
                print(f"Exception during audio download: {str(e)}")
                
            if not download_success:
                continue  # Try again if we have retries left
                
        except Exception as e:
            print(f"Exception during FakeYou processing: {str(e)}")
            # Continue to next retry attempt
    
    # If we get here, all retries have failed
    print(f"All {max_retries} retry attempts failed for {character_name}. Giving up.")
    return None 