import re
from slop_gen.utils.api_utils import openai_chat_api

def generate_conversation_script(input_text, teacher1_name="Professor Sarah", teacher2_name="Professor Michael", duration_seconds=25):
    """
    Generates a conversation script between two teachers based on the input text,
    designed to take 20-30 seconds when read aloud.
    
    Args:
        input_text (str): The educational content to convert to conversation
        teacher1_name (str): Name of the first teacher
        teacher2_name (str): Name of the second teacher
        duration_seconds (int): Target duration in seconds (aim for 20-30 seconds)
        
    Returns:
        list: List of dictionaries with 'speaker' and 'text' keys
    """
    # Estimate word count for the target duration (average speaking rate is ~150 words per minute)
    target_word_count = int((duration_seconds / 60) * 150)
    
    prompt = (
        f"Convert the following educational content into a natural, engaging conversation "
        f"between two professors named {teacher1_name} and {teacher2_name}. "
        f"The conversation should take approximately {duration_seconds} seconds to read aloud (about {target_word_count} words total). "
        "The tone should be clear and professional like university professors. "
        "Each professor should have roughly equal speaking time. "
        "They should speak in first person and address each other by name occasionally. "
        "Alternate between the professors for a natural back-and-forth exchange. "
        "Format the output as a clean script with each line starting with the speaker's name followed by a colon.\n\n"
        f"Content: {input_text}"
    )

    messages = [
        {"role": "system", "content": "You are an expert educational content creator who specializes in creating engaging educational dialogues."},
        {"role": "user", "content": prompt},
    ]

    try:
        script_text = openai_chat_api(messages).strip()
        
        # Parse the conversation into a structured format
        lines = script_text.strip().split('\n')
        conversation = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for standard dialogue format: "Name: Text"
            match = re.match(r'^([^:]+):\s*(.+)$', line)
            if match:
                speaker_name = match.group(1).strip()
                text = match.group(2).strip()
                
                # Normalize speaker names to match the given teacher names
                if speaker_name.lower() in [teacher1_name.lower(), teacher1_name.split()[0].lower()]:
                    speaker_name = teacher1_name
                elif speaker_name.lower() in [teacher2_name.lower(), teacher2_name.split()[0].lower()]:
                    speaker_name = teacher2_name
                
                conversation.append({
                    "speaker": speaker_name,
                    "text": text
                })
        
        return conversation
    except Exception as e:
        print(f"❌ Error generating conversation script: {e}")
        return []

def generate_podcast_script(input_text, duration_seconds=25):
    """
    Generates a podcast-style script based on the input text,
    designed to take 20-30 seconds when read aloud.
    
    Args:
        input_text (str): The educational content to convert to podcast style
        duration_seconds (int): Target duration in seconds (aim for 20-30 seconds)
        
    Returns:
        str: Podcast-style script
    """
    # Estimate word count for the target duration (average speaking rate is ~150 words per minute)
    target_word_count = int((duration_seconds / 60) * 150)
    
    prompt = (
        f"Convert the following educational content into a natural, engaging script "
        f"that would take approximately {duration_seconds} seconds to read aloud (about {target_word_count} words). "
        "The tone should be clear and professional like a university professor. "
        "The content should be spoken in first person from the teacher's perspective. "
        "Don't include any introduction or sign-off phrases - just the core content. "
        "Do not mention your name or refer to yourself as a specific character. "
        "The script should focus only on explaining the content clearly.\n\n"
        f"Content: {input_text}"
    )

    messages = [
        {"role": "system", "content": "You are an expert educational content creator who specializes in converting complex topics into clear, professional explanations."},
        {"role": "user", "content": prompt},
    ]

    try:
        script = openai_chat_api(messages).strip()
        
        # Clean up the response - remove any "Host:" or similar prefixes
        script = re.sub(r'^\s*(Host|Speaker|Teacher|Presenter|Narrator|Professor):\s*', '', script)
        
        return script
    except Exception as e:
        print(f"❌ Error generating podcast script: {e}")
        return f"Failed to generate podcast script: {str(e)}"

def split_content_into_segments(content, segment_duration=10):
    """
    Splits the content into segments of approximately 10 seconds each for image generation.
    
    Args:
        content (str): The podcast script content
        segment_duration (int): Target duration in seconds for each segment
        
    Returns:
        list: List of text segments
    """
    # Estimate word count for each segment (average speaking rate is ~150 words per minute)
    words_per_segment = int((segment_duration / 60) * 150)
    
    words = content.split()
    segments = []
    
    for i in range(0, len(words), words_per_segment):
        segment = " ".join(words[i:i + words_per_segment])
        segments.append(segment)
    
    return segments 