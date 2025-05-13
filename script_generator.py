import re
import argparse
from typing import Tuple, List
from slop_gen.utils.api_utils import openai_chat_api

def estimate_reading_time(text: str) -> float:
    """
    Estimates the reading time in seconds for a given text.
    Uses an average reading speed of 150 words per minute.
    """
    words = len(text.split())
    return (words / 150) * 60

def format_script(script: str) -> List[str]:
    """
    Formats the script by splitting into sentences and cleaning up.
    Returns a list of sentences, each on its own line.
    """
    # Split on sentence endings while preserving the punctuation
    sentences = re.split(r'([.!?])\s+', script)
    
    # Recombine sentences with their punctuation
    formatted_sentences = []
    for i in range(0, len(sentences)-1, 2):
        if i+1 < len(sentences):
            sentence = sentences[i] + sentences[i+1]
        else:
            sentence = sentences[i]
        sentence = sentence.strip()
        if sentence:
            formatted_sentences.append(sentence)
    
    return formatted_sentences

def generate_script(topic: str, duration_seconds: int) -> Tuple[List[str], float]:
    """
    Generates a script based on the given topic and target duration.
    
    Args:
        topic: A string describing the story topic/theme
        duration_seconds: Target duration in seconds (max 120)
    
    Returns:
        Tuple containing:
        - List of sentences forming the script
        - Actual estimated reading time in seconds
    """
    if duration_seconds > 120:
        duration_seconds = 120
    
    prompt = (
        f"Write a short story about '{topic}' that can be read in approximately {duration_seconds} seconds. "
        "Structure the story in three parts:\n"
        "1. Situation: Set up the scene and characters\n"
        "2. Complication: Introduce a problem or conflict\n"
        "3. Resolution: Resolve the situation\n\n"
        "Write in a clear, engaging style suitable for text-to-speech narration. "
        "Each sentence should be concise and impactful. "
        "The total length should be appropriate for a {duration_seconds}-second reading."
    )

    messages = [
        {"role": "system", "content": "You are a professional script writer specializing in short-form storytelling."},
        {"role": "user", "content": prompt},
    ]

    try:
        # First attempt
        script_text = openai_chat_api(messages).strip()
        formatted_script = format_script(script_text)
        reading_time = estimate_reading_time(script_text)
        
        # If too long, try again with adjusted duration
        if reading_time > duration_seconds:
            adjusted_duration = int(duration_seconds * 0.8)  # Reduce target by 20%
            messages.append({"role": "assistant", "content": script_text})
            messages.append({
                "role": "user", 
                "content": f"The previous script was too long. Please write a shorter version targeting {adjusted_duration} seconds."
            })
            
            script_text = openai_chat_api(messages).strip()
            formatted_script = format_script(script_text)
            reading_time = estimate_reading_time(script_text)
        
        return formatted_script, reading_time

    except Exception as e:
        print("❌ Error generating script:", e)
        return ["Failed to generate script."], 0.0

def main():
    parser = argparse.ArgumentParser(description='Generate a script for TTS narration.')
    parser.add_argument('--topic', type=str, required=True,
                      help='The topic or theme for the script (e.g., "A dramatic story about vampires")')
    parser.add_argument('--duration', type=int, required=True,
                      help='Target duration in seconds (max 120)')
    
    args = parser.parse_args()
    
    script, reading_time = generate_script(args.topic, args.duration)
    
    print(f"\nGenerated Script (Estimated reading time: {reading_time:.1f} seconds):")
    print("\n".join(script))

if __name__ == "__main__":
    main()
