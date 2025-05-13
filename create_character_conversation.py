#!/usr/bin/env python3
import os
import argparse
from info_videos.main import generate_conversation_video
from info_videos.image_generator import get_topic_collection

def clean_character_images(character1, character2):
    """Remove existing character images to force regeneration"""
    teachers_dir = "info_videos/assets/teachers"
    if os.path.exists(teachers_dir):
        for filename in os.listdir(teachers_dir):
            if character1.split()[0] in filename or character2.split()[0] in filename:
                file_path = os.path.join(teachers_dir, filename)
                os.remove(file_path)
                print(f"Removed existing file: {file_path}")

def select_voice_for_character(character_name):
    """Select appropriate voice based on character traits"""
    character_lower = character_name.lower()
    
    # Default values
    voice = "alloy"  # Default neutral voice
    pitch = 0        # Default pitch
    style = None     # Default style
    speed = 1.0      # Default speed
    
    # Character-specific adjustments
    if "peter griffin" in character_lower:
        voice = "echo"
        pitch = 0
        style = "standard"
    elif "quagmire" in character_lower:
        voice = "onyx"
        pitch = -2
        style = "standard"
    elif "wendy" in character_lower:
        voice = "alloy"
        pitch = -3
        style = "standard"
    elif "ronald" in character_lower or "mcdonald" in character_lower:
        voice = "onyx"
        pitch = -3
        style = "standard"
    elif "homer" in character_lower:
        voice = "echo"
        pitch = -1
        style = "standard" 
    elif "stewie" in character_lower:
        voice = "fable"
        pitch = 5
        style = "standard"
    
    # Detect gender from common names to adjust if no specific character is matched
    female_indicators = ["woman", "female", "girl", "princess", "queen", "lady", "mrs", "ms", "miss"]
    male_indicators = ["man", "male", "boy", "prince", "king", "mr", "sir"]
    
    if any(indicator in character_lower for indicator in female_indicators):
        voice = "alloy"  # Female voice
    elif any(indicator in character_lower for indicator in male_indicators):
        voice = "echo"   # Male voice
    
    return voice, pitch, style, speed

def main():
    parser = argparse.ArgumentParser(description='Generate a conversation video between two characters on a topic')
    parser.add_argument('--character1', type=str, default="Wendy from Wendy's", 
                        help='Name of the first character (e.g., "Peter Griffin")')
    parser.add_argument('--character2', type=str, default="Ronald McDonald", 
                        help='Name of the second character (e.g., "Quagmire")')
    parser.add_argument('--topic', type=str, required=True, 
                        help='The topic they should talk about (e.g., "the politics of Indonesia")')
    parser.add_argument('--output', type=str, 
                        help='Output file path for the video')
    parser.add_argument('--speech-speed', type=float, default=1.0, 
                        help='Speed of speech (default: 1.0)')
    
    args = parser.parse_args()
    
    # Clean up any existing character images
    clean_character_images(args.character1, args.character2)
    
    # Generate educational content based on the requested topic
    print(f"Generating conversation about: {args.topic}")
    educational_content = args.topic
    
    # Try to generate related image topics
    image_topics = get_topic_collection(args.topic)
    if not image_topics:
        # If no specific collection exists, create generic topics based on the user's input
        image_topics = [
            f"{args.topic} - concept illustration",
            f"{args.topic} - detailed diagram",
            f"{args.topic} - visual representation",
            f"{args.topic} - key elements",
            f"{args.topic} - practical example",
            f"{args.topic} - related concepts"
        ]
    
    # Select appropriate voices and attributes for each character
    char1_voice, char1_pitch, char1_style, char1_speed = select_voice_for_character(args.character1)
    char2_voice, char2_pitch, char2_style, char2_speed = select_voice_for_character(args.character2)
    
    # Default output path if not specified
    if not args.output:
        char1_name = args.character1.split()[0]
        char2_name = args.character2.split()[0]
        output_name = f"{char1_name}_{char2_name}_{args.topic.replace(' ', '_')[:20]}.mp4"
        output_path = f"info_videos/assets/output/{output_name}"
    else:
        output_path = args.output
    
    # Generate the conversation video
    print(f"Generating conversation video between {args.character1} and {args.character2} about {args.topic}")
    video_path = generate_conversation_video(
        teacher1_name=args.character1,
        teacher2_name=args.character2,
        input_text=educational_content,
        output_path=output_path,
        speech_speed=args.speech_speed,
        # Use the selected voices and attributes
        teacher1_voice=char1_voice,
        teacher2_voice=char2_voice,
        teacher1_pitch=char1_pitch,
        teacher2_pitch=char2_pitch,
        teacher1_style=char1_style,
        teacher2_style=char2_style,
        teacher1_speed=char1_speed,
        teacher2_speed=char2_speed,
        # Use image topics for better visuals
        image_topics=image_topics[:6]  # Limit to 6 images
    )
    
    if video_path:
        print(f"\n✅ Success! Conversation video generated at: {video_path}")
    else:
        print("\n❌ Failed! Unable to generate conversation video.")

if __name__ == "__main__":
    main() 