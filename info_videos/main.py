import os
import argparse
from info_videos.image_generator import generate_teacher_image, generate_teachers_images, generate_content_image, generate_topic_images
from info_videos.content_generator import generate_podcast_script, generate_conversation_script, split_content_into_segments
from info_videos.audio_generator import generate_audio_from_text, generate_conversation_audio, list_available_voices, list_available_styles
from info_videos.video_generator import create_info_video, create_conversation_video

def generate_conversation_video(teacher1_name, teacher2_name, input_text, output_path=None, speech_speed=1.3,
                               teacher1_voice="alloy", teacher2_voice="echo", 
                               teacher1_pitch=0, teacher2_pitch=0,
                               teacher1_style=None, teacher2_style=None,
                               teacher1_speed=None, teacher2_speed=None,
                               topic_images=None, image_topics=None, image_duration=10, duration_seconds=25):
    """
    Generate a conversation video with two teachers discussing a topic.
    
    Args:
        teacher1_name (str): Name of the first teacher
        teacher2_name (str): Name of the second teacher
        input_text (str): Educational content text
        output_path (str, optional): Path to save the output video
        speech_speed (float): Default speed factor for both speakers (>1.0 for faster)
        teacher1_voice (str): Voice for first teacher (e.g., "alloy", "echo", "fable")
        teacher2_voice (str): Voice for second teacher (different from first)
        teacher1_pitch (int): Pitch adjustment for first teacher's voice (-10 to 10)
        teacher2_pitch (int): Pitch adjustment for second teacher's voice (-10 to 10)
        teacher1_style (str, optional): Voice style for first teacher (e.g., "excited", "serious")
        teacher2_style (str, optional): Voice style for second teacher
        teacher1_speed (float, optional): Specific speech speed for teacher 1 (overrides speech_speed)
        teacher2_speed (float, optional): Specific speech speed for teacher 2 (overrides speech_speed)
        topic_images (list, optional): List of pre-defined image paths to use
        image_topics (list, optional): List of topics to generate images for (instead of using script segments)
        image_duration (int, optional): Duration in seconds for each content image (default: 10)
        duration_seconds (int, optional): Target duration for the conversation (default: 25)
        
    Returns:
        str: Path to the generated video
    """
    # Import here to avoid circular imports
    from info_videos.fakeyou_audio import CHARACTER_VOICES
    
    print(f"Generating conversation video with teachers: {teacher1_name} and {teacher2_name}")
    
    # Check if the characters can use FakeYou
    teacher1_fakeyou = teacher1_name in CHARACTER_VOICES
    teacher2_fakeyou = teacher2_name in CHARACTER_VOICES
    
    if teacher1_fakeyou:
        print(f"✅ Will use FakeYou for {teacher1_name}")
    if teacher2_fakeyou:
        print(f"✅ Will use FakeYou for {teacher2_name}")
    
    # Create necessary directories
    assets_dir = "info_videos/assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    # 1. Generate teacher images
    print("Generating teacher images...")
    teacher1_image_path, teacher2_image_path = generate_teachers_images(teacher1_name, teacher2_name)
    if not teacher1_image_path or not teacher2_image_path:
        print("❌ Failed to generate one or both teacher images. Aborting.")
        return None
    print(f"✅ Teacher images generated")
    
    # 2. Generate conversation script
    print("Generating conversation script...")
    conversation = generate_conversation_script(input_text, teacher1_name, teacher2_name, duration_seconds=duration_seconds)
    if not conversation:
        print("❌ Failed to generate conversation script. Aborting.")
        return None
    
    # Count words in the conversation
    total_words = sum(len(segment["text"].split()) for segment in conversation)
    print(f"✅ Conversation script generated ({total_words} words, {len(conversation)} exchanges)")
    
    # Use individual speeds if provided, otherwise use default speech_speed
    t1_speed = teacher1_speed if teacher1_speed is not None else speech_speed
    t2_speed = teacher2_speed if teacher2_speed is not None else speech_speed
    
    # 3. Generate audio for each segment of the conversation
    print("Generating conversation audio...")
    audio_dir = os.path.join(assets_dir, "audio", "conversation")
    audio_conversation = generate_conversation_audio(
        conversation=conversation, 
        output_dir=audio_dir, 
        teacher1_voice=teacher1_voice,  
        teacher2_voice=teacher2_voice,
        speed=speech_speed,  # Will be overridden by individual speeds
        teacher1_pitch=teacher1_pitch,
        teacher2_pitch=teacher2_pitch,
        teacher1_style=teacher1_style,
        teacher2_style=teacher2_style,
        teacher1_speed=t1_speed,
        teacher2_speed=t2_speed,
        teacher1_name=teacher1_name,  # Pass the character name for FakeYou
        teacher2_name=teacher2_name   # Pass the character name for FakeYou
    )
    
    if not audio_conversation:
        print("❌ Failed to generate conversation audio. Aborting.")
        return None
    print(f"✅ Conversation audio generated ({len(audio_conversation)} segments)")
    
    # 4. Content images - either use provided images, generate from topics, or from script
    print("Preparing content images...")
    content_image_paths = []
    
    if topic_images and os.path.exists(topic_images[0]):
        # Use pre-defined images if provided
        print("  Using provided topic images")
        content_image_paths = topic_images
        
    elif image_topics:
        # Generate images based on specific topics
        print("  Generating images for specified topics")
        content_image_paths = generate_topic_images(image_topics)
        
    else:
        # Extract text segments for content image generation from the script
        print("  Generating images based on conversation segments")
        text_segments = [segment["text"] for segment in conversation]
        
        # 5. Generate content images (one per exchange)
        for i, segment in enumerate(conversation):
            print(f"  Generating image {i+1}/{len(conversation)}...")
            image_path = generate_content_image(segment["text"])
            content_image_paths.append(image_path)
    
    # Filter out None values (failed image generations)
    content_image_paths = [path for path in content_image_paths if path]
    if not content_image_paths:
        print("❌ Failed to generate any content images. Aborting.")
        return None
    print(f"✅ Using {len(content_image_paths)} content images")
    
    # 6. Create conversation video
    print("Creating conversation video...")
    if not output_path:
        output_path = os.path.join(assets_dir, "output", f"conversation_{teacher1_name.replace(' ', '_')}_{teacher2_name.replace(' ', '_')}.mp4")
    
    video_path = create_conversation_video(
        teacher1_image_path=teacher1_image_path,
        teacher2_image_path=teacher2_image_path,
        audio_conversation=audio_conversation,
        content_image_paths=content_image_paths,
        output_path=output_path,
        image_duration=image_duration
    )
    
    if not video_path:
        print("❌ Failed to create conversation video. Aborting.")
        return None
    
    print(f"✅ Conversation video created successfully: {video_path}")
    return video_path

def generate_info_video(teacher_name, input_text, output_path=None, speech_speed=1.3, 
                      teacher_voice="alloy", teacher_pitch=0, teacher_style=None,
                      topic_images=None, image_topics=None):
    """
    Generate an informational video with a teacher presenting content.
    
    Args:
        teacher_name (str): Name of the teacher (e.g., "Professor Sarah Johnson")
        input_text (str): Educational content text
        output_path (str, optional): Path to save the output video
        speech_speed (float): Speed factor for the speech (>1.0 for faster)
        teacher_voice (str): Voice for the teacher (e.g., "alloy", "echo", "fable")
        teacher_pitch (int): Pitch adjustment for teacher's voice (-10 to 10)
        teacher_style (str, optional): Voice style for the teacher (e.g., "excited", "serious")
        topic_images (list, optional): List of pre-defined image paths to use
        image_topics (list, optional): List of topics to generate images for (instead of using script segments)
        
    Returns:
        str: Path to the generated video
    """
    print(f"Generating informational video with teacher: {teacher_name}")
    
    # Create necessary directories
    assets_dir = "info_videos/assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    # 1. Generate teacher image
    print("Generating teacher image...")
    teacher_image_path = generate_teacher_image(teacher_name)
    if not teacher_image_path:
        print("❌ Failed to generate teacher image. Aborting.")
        return None
    print(f"✅ Teacher image generated: {teacher_image_path}")
    
    # 2. Generate podcast-style script
    print("Generating podcast script...")
    podcast_script = generate_podcast_script(input_text)
    if not podcast_script or podcast_script.startswith("Failed to generate"):
        print("❌ Failed to generate podcast script. Aborting.")
        return None
    print(f"✅ Podcast script generated ({len(podcast_script.split())} words)")
    
    # 3. Generate audio from script, with teacher's voice
    print("Generating audio...")
    audio_output_path = os.path.join(assets_dir, "audio", f"{teacher_name.replace(' ', '_')}_audio.mp3")
    audio_path = generate_audio_from_text(
        podcast_script, 
        audio_output_path, 
        teacher_name=teacher_name, 
        speed=speech_speed,
        voice=teacher_voice,
        pitch=teacher_pitch,
        voice_style=teacher_style
    )
    if not audio_path:
        print("❌ Failed to generate audio. Aborting.")
        return None
    print(f"✅ Audio generated: {audio_path}")
    
    # 4. Split content into segments (this is still needed for timing)
    print("Splitting content into segments...")
    text_segments = split_content_into_segments(podcast_script, segment_duration=10)
    print(f"✅ Content split into {len(text_segments)} segments")
    
    # 5. Prepare content images - either use provided images, generate from topics, or from script
    print("Preparing content images...")
    content_image_paths = []
    
    if topic_images and os.path.exists(topic_images[0]):
        # Use pre-defined images if provided
        print("  Using provided topic images")
        content_image_paths = topic_images
        
    elif image_topics:
        # Generate images based on specific topics
        print("  Generating images for specified topics")
        content_image_paths = generate_topic_images(image_topics)
        
    else:
        # Generate content images for each segment
        print("  Generating images based on script segments")
        for i, segment in enumerate(text_segments):
            print(f"  Generating image {i+1}/{len(text_segments)}...")
            image_path = generate_content_image(segment)
            content_image_paths.append(image_path)
    
    # Filter out None values (failed image generations)
    content_image_paths = [path for path in content_image_paths if path]
    if not content_image_paths:
        print("❌ Failed to generate any content images. Aborting.")
        return None
    print(f"✅ Using {len(content_image_paths)} content images")
    
    # 6. Create video
    print("Creating video...")
    if not output_path:
        output_path = os.path.join(assets_dir, "output", f"{teacher_name.replace(' ', '_')}_info_video.mp4")
    
    video_path = create_info_video(
        teacher_image_path=teacher_image_path,
        content_image_paths=content_image_paths,
        audio_path=audio_path,
        text_segments=text_segments,
        output_path=output_path,
        segment_duration=10
    )
    
    if not video_path:
        print("❌ Failed to create video. Aborting.")
        return None
    
    print(f"✅ Informational video created successfully: {video_path}")
    return video_path

def main():
    parser = argparse.ArgumentParser(description="Generate informational videos with virtual teachers")
    parser.add_argument("--mode", choices=["single", "conversation"], default="single", 
                        help="Video mode: single teacher or conversation between two teachers")
    parser.add_argument("--teacher", help="Name of the teacher for single mode (e.g., 'Professor Sarah Johnson')")
    parser.add_argument("--teacher1", help="Name of the first teacher for conversation mode")
    parser.add_argument("--teacher2", help="Name of the second teacher for conversation mode")
    parser.add_argument("--input", required=True, help="Input text file or string")
    parser.add_argument("--output", help="Output video path")
    parser.add_argument("--speed", type=float, default=1.3, help="Speech speed factor (default: 1.3)")
    
    # Voice options
    parser.add_argument("--teacher-voice", default="alloy", help="Voice for single teacher mode")
    parser.add_argument("--teacher1-voice", default="alloy", help="Voice for first teacher in conversation mode")
    parser.add_argument("--teacher2-voice", default="echo", help="Voice for second teacher in conversation mode")
    
    # Pitch options
    parser.add_argument("--teacher-pitch", type=int, default=0, help="Pitch adjustment for single teacher")
    parser.add_argument("--teacher1-pitch", type=int, default=0, help="Pitch adjustment for first teacher")
    parser.add_argument("--teacher2-pitch", type=int, default=0, help="Pitch adjustment for second teacher")
    
    # Style options
    parser.add_argument("--teacher-style", help="Voice style for single teacher (e.g., excited, serious)")
    parser.add_argument("--teacher1-style", help="Voice style for first teacher")
    parser.add_argument("--teacher2-style", help="Voice style for second teacher")
    
    # Helper flags
    parser.add_argument("--list-voices", action="store_true", help="List available voice options")
    parser.add_argument("--list-styles", action="store_true", help="List available voice style options")
    
    # Image options
    parser.add_argument("--topic-images", nargs="+", help="List of paths to pre-defined content images")
    parser.add_argument("--image-topics", nargs="+", help="List of topics to generate images for")
    
    args = parser.parse_args()
    
    # Check for helper flags first
    if args.list_voices:
        voices = list_available_voices()
        print("\nAvailable voices:")
        for voice, details in voices.items():
            print(f"  - {voice}: {details['description']} ({details['gender']})")
        return
        
    if args.list_styles:
        styles = list_available_styles()
        print("\nAvailable voice styles:")
        for style in styles:
            print(f"  - {style}")
        return
    
    # Check if input is a file or a string
    input_text = ""
    if os.path.exists(args.input):
        with open(args.input, "r") as f:
            input_text = f.read()
    else:
        input_text = args.input
    
    if args.mode == "conversation":
        if not args.teacher1 or not args.teacher2:
            print("❌ For conversation mode, both --teacher1 and --teacher2 are required")
            return
        generate_conversation_video(
            args.teacher1, 
            args.teacher2, 
            input_text, 
            args.output, 
            args.speed,
            teacher1_voice=args.teacher1_voice,
            teacher2_voice=args.teacher2_voice,
            teacher1_pitch=args.teacher1_pitch,
            teacher2_pitch=args.teacher2_pitch,
            teacher1_style=args.teacher1_style,
            teacher2_style=args.teacher2_style,
            teacher1_speed=args.teacher1_speed if hasattr(args, 'teacher1_speed') else None,
            teacher2_speed=args.teacher2_speed if hasattr(args, 'teacher2_speed') else None,
            topic_images=args.topic_images,
            image_topics=args.image_topics
        )
    else:  # single mode
        if not args.teacher:
            print("❌ For single mode, --teacher is required")
            return
        generate_info_video(
            args.teacher, 
            input_text, 
            args.output, 
            args.speed,
            teacher_voice=args.teacher_voice,
            teacher_pitch=args.teacher_pitch,
            teacher_style=args.teacher_style,
            topic_images=args.topic_images,
            image_topics=args.image_topics
        )

if __name__ == "__main__":
    main() 