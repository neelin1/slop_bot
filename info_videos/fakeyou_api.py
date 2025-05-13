import os
import time
import ssl
from fakeyou.fakeyou import FakeYou
from fakeyou.asynchronous_fakeyou import AsyncFakeYou
import asyncio
import requests

# Voice token IDs for characters
CHARACTER_VOICE_TOKENS = {
    "peter griffin": "TM:3sk340a43q6n",  # Peter Griffin
    "homer simpson": "TM:c0caxchqrcwc",  # Homer Simpson
    # Add more characters as needed
}

# FakeYou login credentials
FAKEYOU_USERNAME = "abc123123@gmail.com"
FAKEYOU_PASSWORD = "aaaaaa"

# Create a custom context that doesn't verify certificates
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Monkey patch SSL for requests to disable certificate verification
old_merge_environment_settings = requests.Session.merge_environment_settings

def merge_environment_settings(self, url, proxies, stream, verify, cert):
    settings = old_merge_environment_settings(self, url, proxies, stream, verify, cert)
    settings['verify'] = False
    return settings

requests.Session.merge_environment_settings = merge_environment_settings

class FakeYouSyncWrapper:
    """
    A synchronous wrapper for the FakeYou Python library to handle TTS generation for specific characters
    """
    def __init__(self):
        self.fy = FakeYou()
        self._try_login()
        
    def _try_login(self):
        """Attempt to login if credentials are available"""
        if FAKEYOU_USERNAME and FAKEYOU_PASSWORD:
            try:
                print(f"Attempting to login with username: {FAKEYOU_USERNAME}")
                result = self.fy.login(FAKEYOU_USERNAME, FAKEYOU_PASSWORD)
                if result:
                    print("Successfully logged in to FakeYou")
                else:
                    print("Login failed")
            except Exception as e:
                print(f"Error during login: {e}")
                print("Continuing without login")
        else:
            print("No FakeYou credentials found. Running in anonymous mode.")
        
    def generate_tts(self, text, voice_token, output_path=None):
        """
        Generate TTS audio using FakeYou API synchronously
        
        Args:
            text (str): Text to convert to speech
            voice_token (str): Voice token ID for the character
            output_path (str, optional): Path to save the output audio file
            
        Returns:
            str: Path to the generated audio file or None if failed
        """
        if not output_path:
            # Create a default output path if not provided
            os.makedirs("info_videos/assets/audio", exist_ok=True)
            safe_text = "".join(c if c.isalnum() else "_" for c in text[:20])
            output_path = f"info_videos/assets/audio/fakeyou_{safe_text}_{int(time.time())}.wav"
        
        try:
            print(f"Requesting TTS from FakeYou API for text: '{text[:30]}...'")
            
            # Try using the say method first, which combines job creation and polling
            try:
                print("Using 'say' method for direct TTS generation...")
                result = self.fy.say(text, voice_token)
                if result and isinstance(result, bytes):
                    with open(output_path, 'wb') as f:
                        f.write(result)
                    print(f"TTS audio saved to {output_path}")
                    return output_path
            except Exception as e:
                print(f"Say method failed: {e}")
                print("Falling back to job-based method...")
            
            # Fallback to manual job creation and polling
            print("Making TTS job...")
            job_token = self.fy.make_tts_job(text, voice_token)
            if not job_token:
                print("Failed to create TTS job")
                return None
            
            print(f"TTS job created with token: {job_token}")
            
            # Poll for job completion
            max_attempts = 30
            for attempt in range(max_attempts):
                print(f"Polling job status (attempt {attempt+1}/{max_attempts})...")
                result = self.fy.tts_poll(job_token)
                
                if result and isinstance(result, bytes):
                    # Job completed, save the audio file
                    with open(output_path, 'wb') as f:
                        f.write(result)
                    print(f"TTS audio saved to {output_path}")
                    return output_path
                
                # Wait before polling again
                time.sleep(2)
            
            print("Timed out waiting for TTS completion")
            return None
            
        except Exception as e:
            print(f"Error generating TTS with FakeYou API: {e}")
            return None

class FakeYouAsyncWrapper:
    """
    An asynchronous wrapper for the FakeYou Python library to handle TTS generation for specific characters
    """
    def __init__(self):
        self.fy = AsyncFakeYou(verbose=True)
        
    async def _try_login(self):
        """Attempt to login if credentials are available"""
        if FAKEYOU_USERNAME and FAKEYOU_PASSWORD:
            try:
                print(f"Attempting to login with username: {FAKEYOU_USERNAME}")
                result = await self.fy.login(FAKEYOU_USERNAME, FAKEYOU_PASSWORD)
                if result:
                    print("Successfully logged in to FakeYou")
                else:
                    print("Login failed")
            except Exception as e:
                print(f"Error during login: {e}")
                print("Continuing without login")
        else:
            print("No FakeYou credentials found. Running in anonymous mode.")
        
    async def generate_tts(self, text, voice_token, output_path=None):
        """
        Generate TTS audio using FakeYou API asynchronously
        
        Args:
            text (str): Text to convert to speech
            voice_token (str): Voice token ID for the character
            output_path (str, optional): Path to save the output audio file
            
        Returns:
            str: Path to the generated audio file or None if failed
        """
        if not output_path:
            # Create a default output path if not provided
            os.makedirs("info_videos/assets/audio", exist_ok=True)
            safe_text = "".join(c if c.isalnum() else "_" for c in text[:20])
            output_path = f"info_videos/assets/audio/fakeyou_{safe_text}_{int(time.time())}.wav"
        
        try:
            # Try to login first
            await self._try_login()
            
            print(f"Requesting async TTS from FakeYou API for text: '{text[:30]}...'")
            
            # Use the say method which handles the full TTS process
            result = await self.fy.say(text, voice_token, output_path)
            
            if result:
                print(f"TTS audio saved to {output_path}")
                return output_path
            else:
                print(f"Failed to generate TTS: No result returned")
                return None
            
        except Exception as e:
            print(f"Error generating TTS with async FakeYou API: {e}")
            return None
        finally:
            # Ensure the session is closed properly
            if hasattr(self.fy, '_session') and self.fy._session:
                await self.fy._session.close()

def is_character_supported(character_name):
    """Check if a character is supported by FakeYou API"""
    return character_name.lower() in CHARACTER_VOICE_TOKENS

def generate_character_audio(character_name, text, output_path=None):
    """
    Generate TTS audio for a specific character using FakeYou API
    
    Args:
        character_name (str): Name of the character (e.g., "peter griffin")
        text (str): Text to convert to speech
        output_path (str, optional): Path to save the output audio file
        
    Returns:
        str: Path to the generated audio file or None if failed
    """
    character_name_lower = character_name.lower()
    
    if character_name_lower not in CHARACTER_VOICE_TOKENS:
        print(f"No voice token found for character: {character_name}")
        return None
    
    voice_token = CHARACTER_VOICE_TOKENS[character_name_lower]
    print(f"Generating voice for {character_name} using FakeYou API...")
    
    # Try sync approach first as it's simpler
    try:
        print("Using synchronous FakeYou API...")
        wrapper = FakeYouSyncWrapper()
        result = wrapper.generate_tts(text, voice_token, output_path)
        if result:
            return result
    except Exception as e:
        print(f"Sync TTS generation failed: {e}")
        print("Falling back to async approach...")
    
    # Fall back to async approach
    try:
        print("Using asynchronous FakeYou API...")
        async def run_async_tts():
            wrapper = FakeYouAsyncWrapper()
            return await wrapper.generate_tts(text, voice_token, output_path)
        
        # Run the async function in the event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(run_async_tts())
        finally:
            loop.close()
            
    except Exception as e:
        print(f"Async TTS generation also failed: {e}")
        return None

# Test function to verify the module works
def test_fakeyou():
    """Test the FakeYou wrapper with Peter Griffin and Homer Simpson voices"""
    print("Testing FakeYou API wrapper...")
    
    # Test texts
    character_texts = {
        "peter griffin": "Holy crap, Lois! I'm talking about quantum computing. It's like, you know, computers but they're, like, super weird and confusing.",
        "homer simpson": "Mmm... quantum computing. Is that the one where I can simulate donuts in multiple dimensions? D'oh!"
    }
    
    # Create output directory
    os.makedirs("test_output", exist_ok=True)
    
    # Test each character
    for character, text in character_texts.items():
        print(f"\nTesting TTS for {character}...")
        output_path = f"test_output/{character.replace(' ', '_')}_test.wav"
        
        result = generate_character_audio(character, text, output_path)
        
        if result:
            print(f"✅ Success! Audio generated: {result}")
        else:
            print(f"❌ Failed to generate audio for {character}")

if __name__ == "__main__":
    test_fakeyou() 