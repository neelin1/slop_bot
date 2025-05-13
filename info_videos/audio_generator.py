import os
import subprocess
import json
import requests
from io import BytesIO
from slop_gen.utils.api_utils import text_to_speech, openai_chat_api

# Available OpenAI TTS voices with their characteristics
VOICE_OPTIONS = {
    "alloy": {"description": "Neutral, versatile voice", "gender": "neutral"},
    "echo": {"description": "Deep, resonant voice", "gender": "male"},
    "fable": {"description": "British accent, storytelling voice", "gender": "female"},
    "onyx": {"description": "Deep, authoritative voice", "gender": "male"},
    "nova": {"description": "Energetic, youthful voice", "gender": "female"},
    "shimmer": {"description": "Clear, friendly voice", "gender": "female"}
}

# Voice style/vibe options
VOICE_STYLES = [
    "default",
    "excited",
    "friendly",
    "unfriendly",
    "sad",
    "serious",
    "empathetic",
    "authoritative",
    "whispered"
]

def change_speed_ffmpeg(audio_bytes, speed=1.3, pitch=0, in_fmt="mp3", out_fmt="mp3"):
    """
    Changes the speed and/or pitch of audio using ffmpeg.
    
    Args:
        audio_bytes (bytes): The audio bytes to modify
        speed (float): Speed factor (>1.0 for faster, <1.0 for slower)
        pitch (float): Pitch adjustment in semitones (positive = higher, negative = lower)
        in_fmt (str): Input format
        out_fmt (str): Output format
        
    Returns:
        bytes: The modified audio bytes
    """
    # Build filter based on what needs to be adjusted
    filters = []
    
    # Speed adjustment
    if speed != 1.0:
        filters.append(f"atempo={speed}")
    
    # Pitch adjustment (without changing tempo)
    if pitch != 0:
        filters.append(f"asetrate=44100*2^({pitch}/12),aresample=44100")
    
    # Combine filters if there are multiple
    filter_str = ",".join(filters)
    
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-f", in_fmt,
        "-i", "pipe:0"
    ]
    
    # Add filter if any adjustments are needed
    if filter_str:
        cmd.extend(["-filter:a", filter_str])
    
    cmd.extend([
        "-f", out_fmt,
        "pipe:1",
    ])
    
    proc = subprocess.Popen(cmd,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    
    out, err = proc.communicate(audio_bytes)
    
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {err.decode().strip()}")
    
    return out

def generate_audio_from_text(text, output_file, teacher_name=None, model="openai.tts-hd", voice="alloy", 
                           speed=1.3, pitch=0, tone_modifier=None, voice_style=None):
    """
    Generates audio from text using text-to-speech API with enhanced voice control.
    
    Args:
        text (str): Text to convert to speech
        output_file (str): Path to save the audio file
        teacher_name (str, optional): Name of the teacher to mimic the voice of
        model (str): Text-to-speech model to use
        voice (str): Voice to use for text-to-speech
        speed (float): Speed factor for speech (>1.0 for faster)
        pitch (float): Pitch adjustment in semitones
        tone_modifier (str, optional): Text describing how to modify the voice tone
        voice_style (str, optional): Style/vibe for the voice (e.g., "excited", "serious")
        
    Returns:
        str: Path to the generated audio file
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # List of fallback voices to try if the primary voice fails
    fallback_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    
    # Make sure the requested voice is first in the list
    if voice in fallback_voices:
        fallback_voices.remove(voice)
    fallback_voices.insert(0, voice)
    
    # Flag to track if we've disabled style
    style_disabled = False
    
    # Maximum retries
    max_retries = 3
    
    for retry in range(max_retries):
        try:
            # Build modified text with tone instructions if provided
            modified_text = text
            if tone_modifier:
                # Add tone instructions that the TTS model might pick up on
                modified_text = f"[{tone_modifier}] {text}"
            
            # Generate audio using text-to-speech API
            if voice_style and voice_style != "default" and not style_disabled:
                # Custom implementation to add voice style since our wrapper doesn't support it directly
                try:
                    audio_bytes = custom_tts_with_style(modified_text, model, voice, voice_style)
                except Exception as style_error:
                    print(f"  Style application error: {style_error}")
                    print(f"  Falling back to standard TTS without style")
                    style_disabled = True
                    audio_bytes = text_to_speech(text=modified_text, model=model, voice=voice, fmt="mp3")
            else:
                audio_bytes = text_to_speech(text=modified_text, model=model, voice=voice, fmt="mp3")
            
            # Apply speed and pitch adjustments if needed
            if speed != 1.0 or pitch != 0:
                adjustment_desc = []
                if speed != 1.0:
                    adjustment_desc.append(f"speed {speed}x")
                if pitch != 0:
                    adjustment_desc.append(f"pitch {pitch:+d} semitones")
                
                print(f"  Adjusting audio: {', '.join(adjustment_desc)}...")
                audio_bytes = change_speed_ffmpeg(audio_bytes, speed=speed, pitch=pitch, in_fmt="mp3", out_fmt="mp3")
            
            # Save the audio file
            with open(output_file, "wb") as f:
                f.write(audio_bytes)
            
            return output_file
            
        except Exception as e:
            print(f"  Attempt {retry+1}/{max_retries} failed: {e}")
            
            # Try different strategies based on the error
            if "500" in str(e) or "Server Error" in str(e):
                # Server error, let's try different approaches
                if retry < 1:
                    # First retry: Disable style and try again with same voice
                    print(f"  Server error detected. Retrying without voice style...")
                    style_disabled = True
                else:
                    # Second retry: Try a different voice
                    current_voice_index = min(retry, len(fallback_voices)-1)
                    voice = fallback_voices[current_voice_index]
                    print(f"  Server error persists. Trying with voice: {voice}")
            
            # If this was the last retry, we need to create a dummy audio file
            if retry == max_retries - 1:
                print(f"  All attempts failed. Creating silent audio as fallback.")
                create_silent_audio(output_file, duration=5)  # 5 seconds of silence
                return output_file
    
    return None

def create_silent_audio(output_file, duration=5):
    """
    Creates a silent audio file as a fallback when TTS fails.
    
    Args:
        output_file (str): Path to save the audio file
        duration (int): Duration of silence in seconds
        
    Returns:
        str: Path to the generated audio file
    """
    try:
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=stereo",
            "-t", str(duration),
            "-c:a", "libmp3lame",
            "-b:a", "128k",
            output_file
        ]
        
        subprocess.run(cmd, check=True)
        print(f"  Created silent audio file: {output_file}")
        return output_file
    except Exception as e:
        print(f"  Failed to create silent audio: {e}")
        # Last resort - create an empty file
        with open(output_file, "wb") as f:
            pass
        return output_file

def custom_tts_with_style(text, model, voice, voice_style):
    """
    Custom implementation of text-to-speech with voice style support.
    Uses text modification techniques since direct style API may not be supported.
    Uses a simplified approach to avoid server errors.
    
    Args:
        text (str): Text to convert to speech
        model (str): TTS model to use
        voice (str): Voice to use
        voice_style (str): Style/vibe for the voice
        
    Returns:
        bytes: Raw audio data
    """
    # Map style to simple text prefixes
    style_prefixes = {
        "excited": "Speaking with enthusiasm and excitement: ",
        "friendly": "Speaking in a warm and friendly tone: ",
        "serious": "Speaking in a serious, professional tone: ",
        "sad": "Speaking in a sad, somber tone: ",
        "authoritative": "Speaking with authority and command: ",
        "whispered": "Speaking in a hushed, quiet tone: "
    }
    
    # If style not defined, use default
    if voice_style not in style_prefixes:
        return text_to_speech(text=text, model=model, voice=voice, fmt="mp3")
    
    # Get prefix for the requested style
    prefix = style_prefixes.get(voice_style, "")
    
    # Build a modified text with just a simple prefix
    modified_text = f"{prefix}{text}"
    
    print(f"  Applying voice style: {voice_style}")
    
    try:
        # Generate audio with the modified text
        return text_to_speech(text=modified_text, model=model, voice=voice, fmt="mp3")
    except Exception as e:
        print(f"  Error applying style through text modification: {e}")
        print(f"  Falling back to standard TTS")
        return text_to_speech(text=text, model=model, voice=voice, fmt="mp3")

def generate_conversation_audio(conversation, output_dir, teacher1_voice="alloy", teacher2_voice="echo", 
                              speed=1.3, teacher1_pitch=0, teacher2_pitch=0, 
                              teacher1_tone=None, teacher2_tone=None,
                              teacher1_style=None, teacher2_style=None,
                              teacher1_speed=None, teacher2_speed=None):
    """
    Generates audio files for a conversation between two teachers with enhanced voice control.
    
    Args:
        conversation (list): List of dictionaries with 'speaker' and 'text' keys
        output_dir (str): Directory to save the audio files
        teacher1_voice (str): Voice for the first teacher
        teacher2_voice (str): Voice for the second teacher
        speed (float): Default speed factor for speech (if individual speeds aren't specified)
        teacher1_pitch (float): Pitch adjustment for first teacher
        teacher2_pitch (float): Pitch adjustment for second teacher
        teacher1_tone (str, optional): Tone descriptor for first teacher
        teacher2_tone (str, optional): Tone descriptor for second teacher
        teacher1_style (str, optional): Voice style/vibe for first teacher
        teacher2_style (str, optional): Voice style/vibe for second teacher
        teacher1_speed (float, optional): Specific speech speed for teacher 1
        teacher2_speed (float, optional): Specific speech speed for teacher 2
        
    Returns:
        list: List of dictionaries with 'speaker', 'text', and 'audio_path' keys
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Add audio paths to the conversation
    audio_conversation = []
    
    # Print voice information
    print(f"  Voice for Teacher 1: {teacher1_voice}" + 
          (f" ({VOICE_OPTIONS.get(teacher1_voice, {}).get('description', '')})" if teacher1_voice in VOICE_OPTIONS else ""))
    if teacher1_style:
        print(f"  Voice style for Teacher 1: {teacher1_style}")
    if teacher1_speed is not None:
        print(f"  Speech speed for Teacher 1: {teacher1_speed}x")
        
    print(f"  Voice for Teacher 2: {teacher2_voice}" + 
          (f" ({VOICE_OPTIONS.get(teacher2_voice, {}).get('description', '')})" if teacher2_voice in VOICE_OPTIONS else ""))
    if teacher2_style:
        print(f"  Voice style for Teacher 2: {teacher2_style}")
    if teacher2_speed is not None:
        print(f"  Speech speed for Teacher 2: {teacher2_speed}x")
    
    for i, segment in enumerate(conversation):
        speaker = segment["speaker"]
        text = segment["text"]
        
        # Choose voice parameters based on speaker
        if speaker == conversation[0]["speaker"]:  # Teacher 1
            voice = teacher1_voice
            pitch = teacher1_pitch
            tone = teacher1_tone
            style = teacher1_style
            speaker_speed = teacher1_speed if teacher1_speed is not None else speed
        else:  # Teacher 2
            voice = teacher2_voice
            pitch = teacher2_pitch
            tone = teacher2_tone
            style = teacher2_style
            speaker_speed = teacher2_speed if teacher2_speed is not None else speed
            
        # Generate audio file name
        audio_path = os.path.join(output_dir, f"segment_{i+1}_{speaker.replace(' ', '_')}.mp3")
        
        # Generate audio
        print(f"  Generating audio for {speaker}, segment {i+1}/{len(conversation)}...")
        audio_file = generate_audio_from_text(
            text=text,
            output_file=audio_path,
            voice=voice,
            speed=speaker_speed,
            pitch=pitch,
            tone_modifier=tone,
            voice_style=style
        )
        
        if audio_file:
            audio_conversation.append({
                "speaker": speaker,
                "text": text,
                "audio_path": audio_file
            })
    
    return audio_conversation

def list_available_voices():
    """Returns a list of available voice options with their descriptions."""
    return VOICE_OPTIONS

def list_available_styles():
    """Returns a list of available voice style options."""
    return VOICE_STYLES 