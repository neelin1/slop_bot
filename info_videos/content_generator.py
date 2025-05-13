import re
from slop_gen.utils.api_utils import openai_chat_api

def generate_conversation_script(input_text, teacher1_name="Professor Sarah", teacher2_name="Professor Michael", duration_seconds=25, is_summary_mode=False):
    """
    Generates a conversation script between two teachers based on the input text,
    designed to take the specified number of seconds when read aloud.
    
    Args:
        input_text (str): The educational content to convert to conversation
        teacher1_name (str): Name of the first teacher
        teacher2_name (str): Name of the second teacher
        duration_seconds (int): Target duration in seconds
        is_summary_mode (bool): Whether to generate summarized content (True) or detailed technical content (False)
        
    Returns:
        list: List of dictionaries with 'speaker' and 'text' keys
    """
    # Calculate word count more accurately - 3 words per second is a better estimate for conversational speech
    # This is higher than the previous estimate to ensure we get enough content
    target_word_count = int(duration_seconds * 3)
    min_exchanges = max(6, duration_seconds // 10)  # At least 6 exchanges or 1 per 10 seconds
    
    # Define style of conversation based on mode
    if is_summary_mode:
        style_instructions = (
            f"11. Characters should focus on providing a clear and concise summary of the topic\n"
            f"12. Avoid deep technical details and complex jargon - make the content accessible\n"
            f"13. Present key points, main ideas, and essential concepts in simple terms\n"
            f"14. Characters should use relatable examples, analogies, and high-level explanations\n"
            f"15. The conversation should feel like an informative summary for a general audience\n"
        )
        system_role = "You are an expert educator who creates engaging, accessible educational content for general audiences. You excel at summarizing complex topics into clear, concise conversations that capture key points without overwhelming technical details. Your dialogues are informative yet approachable, using plain language that maintains accuracy while being easy to understand."
    else:
        style_instructions = (
            f"11. Characters MUST focus intensely on technical details and scientific concepts - they are experts on this topic\n"
            f"12. Make the conversation technically detailed with accurate terminology, statistics and precise explanations\n"
            f"13. Keep the characters STRICTLY ON TOPIC at all times - no tangents, jokes, or off-topic comments\n"
            f"14. Characters must discuss the topic with rigorous technical depth even if it seems unusual for them\n"
            f"15. The conversation should feel like an expert technical discussion with precise references to concepts from the content\n"
        )
        system_role = "You are an expert technical scriptwriter who creates precisely timed educational dialogue for specialists and academics. You create expert-level technical content with precise terminology, detailed explanations, and academic rigor. Your dialogues never simplify concepts and maintain extremely focused technical discussions. Never include stage directions, actions, or emotional cues - only pure technical dialogue between experts."
    
    prompt = (
        f"Convert the following content into a natural, engaging conversation "
        f"between {teacher1_name} and {teacher2_name}.\n\n"
        f"IMPORTANT REQUIREMENTS:\n"
        f"1. The conversation MUST be EXACTLY {duration_seconds} seconds long when read aloud\n"
        f"2. Include approximately {target_word_count} total words (this is about 3 words per second)\n"
        f"3. Create at least {min_exchanges} back-and-forth exchanges between the speakers\n"
        f"4. Each speaker should talk roughly the same amount (equal word count)\n"
        f"5. Speakers should address each other by name occasionally\n"
        f"6. Format as a clean script with each line starting with speaker's name followed by colon\n"
        f"7. Content should be detailed and substantive\n"
        f"8. DO NOT include any stage directions, actions, or emotional cues in parentheses or brackets\n"
        f"9. Do not use '(laughs)', '(nods)', '(smiling)', or any other action descriptions\n"
        f"10. Include ONLY the spoken dialogue with no descriptions of actions or emotions\n"
        f"{style_instructions}\n"
        f"Content: {input_text}"
    )

    messages = [
        {"role": "system", "content": system_role},
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
                
                # Remove any stage directions that might have been included despite instructions
                text = re.sub(r'\([^)]*\)', '', text)  # Remove text in parentheses
                text = re.sub(r'\[[^\]]*\]', '', text)  # Remove text in brackets
                text = text.strip()
                
                conversation.append({
                    "speaker": speaker_name,
                    "text": text
                })
        
        # Check if we have enough exchanges, if not, try to generate more content
        if len(conversation) < min_exchanges // 2:
            print(f"⚠️ Warning: Generated only {len(conversation)} exchanges, which is less than the target {min_exchanges}.")
            print("   Attempting to generate a more detailed conversation...")
            
            # Define retry style based on mode
            if is_summary_mode:
                retry_style = (
                    f"11. Characters should present a CLEAR SUMMARY of the topic with essential points\n"
                    f"12. Focus on ACCESSIBLE explanations that avoid unnecessary jargon\n"
                    f"13. Make concepts EASY TO UNDERSTAND for a general audience\n"
                    f"14. Use RELATABLE EXAMPLES and analogies to explain complex ideas\n"
                    f"15. Balance ACCURACY with ACCESSIBILITY - be correct but not overwhelmingly technical\n"
                    f"16. Characters should use PLAIN LANGUAGE while maintaining substantive content\n"
                    f"17. The conversation should be INFORMATIVE yet APPROACHABLE\n"
                )
            else:
                retry_style = (
                    f"11. Characters MUST speak as technical subject matter experts with precise terminology\n"
                    f"12. FOCUS EXCLUSIVELY on technical details, data, scientific explanations, methodologies, and deep analysis\n"
                    f"13. Characters MUST NEVER go off topic or include tangents - maintain STRICT focus on the technical content\n"
                    f"14. Conversation should include numerical data, technical terms, methodological details, and specific references\n"
                    f"15. The technical detail must be accurate, precise, and extremely thorough - NO simplification allowed\n"
                    f"16. Characters should correct each other with even more technical details when appropriate\n"
                    f"17. Avoid all casual conversation, jokes, or simplified explanations - ONLY pure technical discussion\n"
                )
            
            # More forceful prompt
            messages[1]["content"] = (
                f"Create a VERY DETAILED conversation between {teacher1_name} and {teacher2_name} about:\n\n{input_text}\n\n"
                f"STRICT REQUIREMENTS:\n"
                f"1. The conversation MUST be EXACTLY {duration_seconds} seconds in duration when read aloud\n"
                f"2. MUST contain {target_word_count} total words (3 words per second)\n"
                f"3. MUST have at least {min_exchanges} exchanges (alternating speakers)\n"
                f"4. Each person MUST speak roughly the same number of words\n"
                f"5. They MUST address each other by name occasionally\n"
                f"6. Format each line as: [Name]: [Text]\n"
                f"7. Make content VERY detailed and comprehensive\n"
                f"8. Do NOT include any meta instructions or notes in the output\n"
                f"9. NEVER include stage directions, actions, or emotions in parentheses or brackets\n"
                f"10. ONLY include dialogue with no descriptions of actions, gestures, or emotions\n"
                f"{retry_style}"
            )
            
            # Try again with the more forceful prompt
            script_text = openai_chat_api(messages).strip()
            lines = script_text.strip().split('\n')
            conversation = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check for standard dialogue format again
                match = re.match(r'^([^:]+):\s*(.+)$', line)
                if match:
                    speaker_name = match.group(1).strip()
                    text = match.group(2).strip()
                    
                    # Normalize speaker names to match the given teacher names
                    if speaker_name.lower() in [teacher1_name.lower(), teacher1_name.split()[0].lower()]:
                        speaker_name = teacher1_name
                    elif speaker_name.lower() in [teacher2_name.lower(), teacher2_name.split()[0].lower()]:
                        speaker_name = teacher2_name
                    
                    # Remove any stage directions that might have been included despite instructions
                    text = re.sub(r'\([^)]*\)', '', text)  # Remove text in parentheses
                    text = re.sub(r'\[[^\]]*\]', '', text)  # Remove text in brackets
                    text = text.strip()
                    
                    conversation.append({
                        "speaker": speaker_name,
                        "text": text
                    })
        
        # Calculate total word count for verification
        total_words = sum(len(segment["text"].split()) for segment in conversation)
        print(f"Generated conversation with {total_words} words in {len(conversation)} exchanges")
        print(f"Target was {target_word_count} words for {duration_seconds} seconds")
        
        return conversation
    except Exception as e:
        print(f"❌ Error generating conversation script: {e}")
        return []

def generate_podcast_script(input_text, duration_seconds=25):
    """
    Generates a podcast-style script based on the input text,
    designed to take the specified number of seconds when read aloud.
    
    Args:
        input_text (str): The educational content to convert to podcast style
        duration_seconds (int): Target duration in seconds
        
    Returns:
        str: Podcast-style script
    """
    # Calculate target word count more accurately (3 words per second)
    target_word_count = int(duration_seconds * 3)
    
    prompt = (
        f"Convert the following content into a natural, engaging script "
        f"that would take EXACTLY {duration_seconds} seconds to read aloud "
        f"(exactly {target_word_count} words total, at 3 words per second). "
        "The tone should be clear and professional like a university professor. "
        "The content should be spoken in first person from the teacher's perspective. "
        "Don't include any introduction or sign-off phrases - just the core content. "
        "Do not mention your name or refer to yourself as a specific character. "
        "The script should focus only on explaining the content clearly.\n\n"
        f"Content: {input_text}"
    )

    messages = [
        {"role": "system", "content": "You are an expert educational content creator who specializes in converting complex topics into clear, professional explanations with precise timing."},
        {"role": "user", "content": prompt},
    ]

    try:
        script = openai_chat_api(messages).strip()
        
        # Clean up the response - remove any "Host:" or similar prefixes
        script = re.sub(r'^\s*(Host|Speaker|Teacher|Presenter|Narrator|Professor):\s*', '', script)
        
        # Verify word count for debugging
        word_count = len(script.split())
        print(f"Generated podcast script with {word_count} words for target of {target_word_count} words")
        
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
    # Calculate words per segment using 3 words per second
    words_per_segment = int(segment_duration * 3)
    
    words = content.split()
    segments = []
    
    for i in range(0, len(words), words_per_segment):
        segment = " ".join(words[i:i + words_per_segment])
        segments.append(segment)
    
    return segments 