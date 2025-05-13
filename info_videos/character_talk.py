#!/usr/bin/env python3
import os
import sys
import argparse
import re

# Add the parent directory to sys.path so that imports work correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from info_videos.main import generate_conversation_video
from info_videos.image_generator import get_topic_collection
from info_videos.utils import extract_text_from_pdf, verify_image_files

def generate_character_conversation():
    """
    Generate a conversation video between two characters about a specific topic.
    
    Example:
        $ python character_talk.py --prompt "Peter Griffin talking to Quagmire about the politics of Indonesia"
    """
    parser = argparse.ArgumentParser(description='Generate a character conversation video based on a prompt')
    parser.add_argument('--prompt', type=str, 
                        help='Prompt describing the conversation (e.g., "Peter Griffin talking to Quagmire about the politics of Indonesia")')
    parser.add_argument('--pdf', type=str,
                        help='Path to a PDF file to use as educational content')
    parser.add_argument('--custom-images', type=str, nargs='+',
                        help='Paths to custom image files to use instead of generating images')
    parser.add_argument('--speech-speed', type=float, default=1.0, 
                        help='Speed of speech (default: 1.0)')
    parser.add_argument('--duration', type=int, default=30,
                        help='Target duration in seconds (default: 30, max recommended: 120)')
    parser.add_argument('--no-fallback', action='store_true',
                        help='Disable fallback voices when FakeYou fails (will result in silent segments)')
    parser.add_argument('--summary-mode', action='store_true',
                        help='Generate summarized content instead of detailed technical content')
    
    args = parser.parse_args()
    
    # Check that at least one of --prompt or --pdf is provided
    if not args.prompt and not args.pdf:
        parser.error("At least one of --prompt or --pdf must be provided")
    
    # Extract content from PDF if provided
    pdf_content = None
    if args.pdf:
        try:
            print(f"Extracting content from PDF: {args.pdf}")
            pdf_content = extract_text_from_pdf(args.pdf)
            print(f"Successfully extracted {len(pdf_content.split())} words from PDF")
        except Exception as e:
            print(f"Error processing PDF file: {e}")
            return
    
    # Verify custom images if provided
    custom_images = None
    if args.custom_images:
        print(f"Verifying {len(args.custom_images)} custom images...")
        custom_images = verify_image_files(args.custom_images)
        print(f"Found {len(custom_images)} valid image files")
    
    # Process prompt if provided, or use a generic one for PDF content
    if args.prompt:
        prompt = args.prompt.lower()
        
        # Extract characters and topic from the prompt
        character1 = "Wendy from Wendy's"  # Default
        character2 = "Ronald McDonald"     # Default
        topic = prompt
        
        # List of known characters (used only for voice selection, not for limiting character choices)
        known_characters = [
            "peter griffin", "quagmire", "homer simpson", "bart simpson", 
            "stewie griffin", "wendy", "ronald mcdonald", "mickey mouse", 
            "donald duck", "cercei lannister", "john pork", "eric cartman"
        ]
        
        # Look for character patterns like "X talking to Y about Z"
        # Note: using the global re module, no need to import it here
        
        # Create a comprehensive pattern for different conversation types
        conversation_keywords = (
            r'(?:talking|speaking|chatting|conversing|discussing|debating|arguing|fighting|'
            r'disagreeing|agreeing|negotiating|brainstorming|dialoguing|conferring|'
            r'consulting|interviewing|confronting|questioning|interrogating|explaining|'
            r'teaching|instructing|lecturing|educating|informing|presenting|'
            r'pitching|selling|convincing|persuading)'
        )
        
        relation_words = (
            r'(?:to|with|against|alongside|beside|opposite|versus|vs|and)'
        )
        
        # Pattern 1: "X talking to Y about Z" - improved to capture multi-word names
        talk_pattern = re.compile(f'((?:[\\w]+\\s?)+)\\s+{conversation_keywords}\\s+{relation_words}\\s+((?:[\\w]+\\s?)+)(?:\\s+about\\s+(.*)|$)', re.IGNORECASE)
        match = talk_pattern.match(prompt)
        
        # Pattern 2: "X and Y discussing Z" - improved to capture multi-word names
        if not match:
            joint_pattern = re.compile(r'((?:[\w]+\s?)+)\s+and\s+((?:[\w]+\s?)+)\s+(?:discussing|talking about|debating|arguing about)\s+(.*)', re.IGNORECASE)
            match = joint_pattern.match(prompt)
            
        # Pattern 3: "X vs Y on the topic of Z" - improved to capture multi-word names
        if not match:
            versus_pattern = re.compile(r'((?:[\w]+\s?)+)\s+(?:vs|versus|against|opposing)\s+((?:[\w]+\s?)+)\s+(?:on|about|regarding|concerning|discussing)\s+(.*)', re.IGNORECASE)
            match = versus_pattern.match(prompt)
        
        # Pattern 4: "X talking to Y" (without a specific topic) - improved to capture multi-word names
        if not match:
            simple_pattern = re.compile(f'((?:[\\w]+\\s?)+)\\s+{conversation_keywords}\\s+{relation_words}\\s+((?:[\\w]+\\s?)+)(?:\\s+|$)', re.IGNORECASE)
            match = simple_pattern.match(prompt)
        
        if match:
            # Extract characters and topic directly from the user's prompt
            character1 = match.group(1).strip()
            character2 = match.group(2).strip()
            
            # Extract topic if there is one (pattern 4 doesn't have a topic group)
            if len(match.groups()) > 2 and match.group(3):
                topic = match.group(3).strip()
            else:
                # If no specific topic, use the entire prompt as the topic
                topic = prompt
            
            # Capitalize character names for better display
            character1 = character1.title()
            character2 = character2.title()
            
            print(f"Extracted characters: '{character1}' and '{character2}'")
            print(f"Extracted topic: '{topic}'")
    else:
        # Using PDF content, let's use default characters and extract topic from filename
        character1 = "Peter Griffin"  # Default for PDF mode
        character2 = "Homer Simpson"  # Default for PDF mode
        pdf_filename = os.path.basename(args.pdf)
        topic = os.path.splitext(pdf_filename)[0].replace('_', ' ').title()
        print(f"Using default characters: '{character1}' and '{character2}'")
        print(f"Using topic from PDF filename: '{topic}'")
    
    # If using a PDF, but also provided a prompt, check if we can extract characters from the prompt
    if args.pdf and args.prompt:
        prompt = args.prompt.lower()
        
        # Define patterns just for character extraction without requiring topic
        simple_relation = f'((?:[\\w]+\\s?)+)\\s+(?:{conversation_keywords}|and)\\s+{relation_words}\\s+((?:[\\w]+\\s?)+)(?:\\s|$)'
        simple_pattern = re.compile(simple_relation, re.IGNORECASE)
        match = simple_pattern.match(prompt)
        
        if match:
            # Extract just the first one or two words for character names to avoid capturing extra text
            char1_raw = match.group(1).strip().split()
            char2_raw = match.group(2).strip().split()
            
            # For better character name extraction, favor two-word names if available
            if len(char1_raw) >= 2:
                character1 = f"{char1_raw[0]} {char1_raw[1]}".title()
            else:
                character1 = char1_raw[0].title()
                
            if len(char2_raw) >= 2:
                character2 = f"{char2_raw[0]} {char2_raw[1]}".title()
            else:
                character2 = char2_raw[0].title()
            
            # Special case handling for common characters
            if character1.lower() == "stewie":
                character1 = "Stewie Griffin"
            elif character2.lower() == "stewie":
                character2 = "Stewie Griffin"
            elif character1.lower() == "peter":
                character1 = "Peter Griffin"
            elif character2.lower() == "peter":
                character2 = "Peter Griffin"
            elif character1.lower() == "mickey":
                character1 = "Mickey Mouse"
            elif character2.lower() == "mickey":
                character2 = "Mickey Mouse"
            elif character1.lower() == "homer":
                character1 = "Homer Simpson"
            elif character2.lower() == "homer":
                character2 = "Homer Simpson"
            elif character1.lower() == "eric":
                character1 = "Eric Cartman"
            elif character2.lower() == "eric":
                character2 = "Eric Cartman"
            
            print(f"Using characters from prompt: '{character1}' and '{character2}'")
            # Keep the topic from PDF filename
        else:
            # Check if prompt just lists two characters
            parts = prompt.split()
            if len(parts) >= 2:
                possible_characters = []
                
                # Look for character names in CHARACTER_VOICES
                from info_videos.fakeyou_audio import CHARACTER_VOICES
                
                for name in CHARACTER_VOICES.keys():
                    name_lower = name.lower()
                    if name_lower in prompt.lower():
                        possible_characters.append(name)
                
                # If we found characters in the prompt
                if len(possible_characters) >= 2:
                    character1 = possible_characters[0]
                    character2 = possible_characters[1]
                    print(f"Using characters from prompt: '{character1}' and '{character2}'")
                elif len(possible_characters) == 1:
                    character1 = possible_characters[0]
                    print(f"Using character from prompt: '{character1}' (keeping '{character2}' as default)")
    
    # Clean up any existing character images
    teachers_dir = "info_videos/assets/teachers"
    if os.path.exists(teachers_dir):
        for filename in os.listdir(teachers_dir):
            # Try to match the first word of each character name to clean up existing images
            char1_first_word = character1.split()[0].lower()
            char2_first_word = character2.split()[0].lower()
            
            if char1_first_word in filename.lower() or char2_first_word in filename.lower():
                file_path = os.path.join(teachers_dir, filename)
                os.remove(file_path)
                print(f"Removed existing file: {file_path}")
    
    # Either use custom images or generate image topics
    image_topics = []
    if custom_images:
        print(f"Using {len(custom_images)} custom images instead of generating new ones")
        # Skip image topic generation - we'll use custom images directly
    elif args.pdf:
        # When using PDF mode, try to use LLM sample images related to the topic
        print(f"Looking for sample LLM images for {topic}")
        sample_dir = "sample_images"
        sample_images = []
        
        if os.path.exists(sample_dir):
            # Search for related images in the sample_images directory
            for filename in os.listdir(sample_dir):
                file_path = os.path.join(sample_dir, filename)
                if os.path.isfile(file_path) and any(ext in filename.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                    # Look for images with related topic in filename
                    topic_words = topic.lower().split()
                    # Add the file if any of the topic words are in the filename
                    if any(word.lower() in filename.lower() for word in topic_words):
                        sample_images.append(file_path)
                        print(f"  Found related sample image: {filename}")
        
        if sample_images:
            custom_images = sample_images
            print(f"Using {len(custom_images)} related sample images instead of generating new ones")
    
    # Either use custom images or generate image topics
    image_topics = []
    if custom_images:
        print(f"Using {len(custom_images)} custom images instead of generating new ones")
        # Skip image topic generation - we'll use custom images directly
    else:
        # Calculate how many images we need based on duration (roughly 1 image per 10 seconds)
        num_images = max(1, min(12, args.duration // 10))
        
        print(f"Generating image topics based on: {topic}")
        image_topics = get_topic_collection(topic)
        if not image_topics or len(image_topics) < num_images:
            # Create generic topics based on the topic
            generated_topics = [
                f"{topic} - concept illustration",
                f"{topic} - detailed diagram",
                f"{topic} - visual representation",
                f"{topic} - key elements",
                f"{topic} - practical example",
                f"{topic} - related concepts",
                f"{topic} - historical context",
                f"{topic} - modern applications",
                f"{topic} - future implications",
                f"{topic} - global perspective",
                f"{topic} - detailed analysis",
                f"{topic} - summary visualization"
            ]
            
            # If we have some but not enough topics from get_topic_collection, supplement with generated ones
            if image_topics:
                image_topics.extend(generated_topics[:num_images - len(image_topics)])
            else:
                image_topics = generated_topics[:num_images]
        else:
            # Limit the collected topics to the number we need
            image_topics = image_topics[:num_images]
        
        print(f"Created {len(image_topics)} image topics")
    
    # Select appropriate voices and attributes for each character
    def select_voice(char_name):
        char_lower = char_name.lower()
        
        # Default values
        voice = "alloy"  # Default neutral voice
        pitch = 0        # Default pitch
        style = None     # Default style
        speed = 1.0      # Default speed
        
        # Character-specific adjustments for known characters
        if "peter griffin" in char_lower:
            voice = "echo"
            pitch = 0
            style = "standard"
        elif "quagmire" in char_lower:
            voice = "onyx"
            pitch = -2
            style = "standard"
        elif "wendy" in char_lower:
            voice = "alloy"
            pitch = -3
            style = "standard"
        elif "ronald" in char_lower or "mcdonald" in char_lower:
            voice = "onyx"
            pitch = -3
            style = "standard"
        elif "homer" in char_lower:
            voice = "echo"
            pitch = -1
            style = "standard" 
        elif "stewie" in char_lower:
            voice = "fable"
            pitch = 5
            style = "standard"
        elif "eric cartman" in char_lower or "cartman" in char_lower:
            voice = "fable"  # Child-like voice
            pitch = 3        # Higher pitch for child character
            style = "standard"
        else:
            # For unknown characters, try to infer voice based on character traits
            # Check for common gender indicators
            female_indicators = ["woman", "female", "girl", "princess", "queen", "lady", "mrs", "ms", "miss", "mother", 
                                "daughter", "sister", "aunt", "grandma", "grandmother", "wife", "goddess"]
            male_indicators = ["man", "male", "boy", "prince", "king", "mr", "sir", "father", "dad", "son", 
                              "brother", "uncle", "grandpa", "grandfather", "husband", "god"]
            
            # Check for age indicators
            child_indicators = ["child", "kid", "baby", "infant", "toddler", "young", "little", "small", "tiny"]
            elderly_indicators = ["elder", "old", "ancient", "senior", "aged", "elderly"]
            
            # Check for character type indicators
            monster_indicators = ["monster", "beast", "creature", "demon", "dragon", "alien", "zombie", "ghost"]
            robot_indicators = ["robot", "android", "machine", "ai", "artificial", "cyborg", "mechanical"]
            animal_indicators = ["dog", "cat", "wolf", "bear", "lion", "tiger", "fox", "animal", "bird", "fish"]
            
            # Determine gender
            if any(indicator in char_lower for indicator in female_indicators):
                voice = "alloy"  # Female voice
            elif any(indicator in char_lower for indicator in male_indicators):
                voice = "echo"   # Male voice
            
            # Adjust pitch based on age/type
            if any(indicator in char_lower for indicator in child_indicators):
                pitch = 3  # Higher pitch for children
                if "boy" in char_lower or any(m_ind in char_lower for m_ind in male_indicators):
                    voice = "fable"  # Child-like voice
            elif any(indicator in char_lower for indicator in elderly_indicators):
                pitch = -2  # Lower pitch for elderly
            elif any(indicator in char_lower for indicator in monster_indicators):
                voice = "onyx"
                pitch = -4  # Very low for monsters
            elif any(indicator in char_lower for indicator in robot_indicators):
                voice = "echo"
                pitch = -1  # Slight robotic tone
            elif any(indicator in char_lower for indicator in animal_indicators):
                # Animals get varied voices
                if "small" in char_lower or "tiny" in char_lower:
                    pitch = 2  # Small animals get higher pitch
                else:
                    pitch = -2  # Large animals get lower pitch
        
        return voice, pitch, style, speed
    
    char1_voice, char1_pitch, char1_style, char1_speed = select_voice(character1)
    char2_voice, char2_pitch, char2_style, char2_speed = select_voice(character2)
    
    # Generate output file name
    char1_name = character1.split()[0]
    char2_name = character2.split()[0]
    topic_short = re.sub(r'[^\w\s]', '', topic).replace(' ', '_')[:20]
    output_path = f"info_videos/assets/output/{char1_name}_{char2_name}_{topic_short}.mp4"
    
    # Print summary of what we're generating
    print(f"\n📽️ Generating conversation video:")
    print(f"  • Character 1: {character1} (Voice: {char1_voice}, Pitch: {char1_pitch})")
    print(f"  • Character 2: {character2} (Voice: {char2_voice}, Pitch: {char2_pitch})")
    print(f"  • Topic: {topic}")
    print(f"  • Target Duration: {args.duration} seconds")
    if custom_images:
        print(f"  • Images: {len(custom_images)} custom images")
    else:
        print(f"  • Images: {len(image_topics)} generated topics")
    print(f"  • Output: {output_path}")
    if args.no_fallback:
        print(f"  • Fallback voices: Disabled")
    print(f"  • Mode: {'Summary' if args.summary_mode else 'Technical details'}")
    print()
    
    # Generate a longer input text for the conversation based on the desired duration
    # Calculate word count based on desired duration - aim for more words than needed
    # to ensure the conversation is long enough
    target_word_count = args.duration * 3  # Approximately 3 words per second
    
    # Create a more detailed prompt that explicitly states the number of exchanges needed
    # The number of exchanges should be at least the number of images to ensure all images are used
    min_exchanges = max(4, len(image_topics) if image_topics else 4)
    
    # Use PDF content if provided, otherwise generate from the topic
    if pdf_content:
        input_text = f"Create a conversation between {character1} and {character2} discussing the following educational content:\n\n{pdf_content}\n\n"
        input_text += f"The conversation should be EXACTLY {args.duration} seconds long when read aloud, "
        input_text += f"with approximately {target_word_count} total words. "
        input_text += f"Include at least {min_exchanges} exchanges between the characters (back-and-forth). "
        input_text += f"Make sure both characters speak roughly equal amounts. "
        input_text += f"Each character should have authentic personality and speech patterns. "
        input_text += f"The characters should refer to each other by name occasionally and have a natural conversation flow."
    else:
        input_text = (
            f"Create a conversation between {character1} and {character2} discussing: {topic}. "
            f"The conversation should be EXACTLY {args.duration} seconds long when read aloud, "
            f"with approximately {target_word_count} total words. "
            f"Include at least {min_exchanges} exchanges between the characters (back-and-forth). "
            f"Make sure both characters speak roughly equal amounts. "
            f"Each character should have authentic personality and speech patterns. "
            f"The characters should refer to each other by name occasionally and have a natural conversation flow. "
            f"Include specific details, examples, and perspectives on the topic."
        )
    
    # Generate the conversation video
    video_path = generate_conversation_video(
        teacher1_name=character1,
        teacher2_name=character2,
        input_text=input_text,
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
        # Pass either custom images or image topics
        topic_images=custom_images,
        image_topics=None if custom_images else image_topics,
        # Set image duration based on total duration and number of images
        image_duration=max(5, min(15, args.duration // (len(custom_images) if custom_images else len(image_topics)))),
        # Pass the requested duration
        duration_seconds=args.duration,
        # Pass the no_fallback setting
        use_fallback_for_failed=not args.no_fallback,
        # Pass the summary mode
        is_summary_mode=args.summary_mode
    )
    
    if video_path:
        print(f"\n✅ Success! Conversation video generated at: {video_path}")
        print(f"Run this to play the video:\n  open {video_path}")
    else:
        print("\n❌ Failed! Unable to generate conversation video.")

if __name__ == "__main__":
    generate_character_conversation() 