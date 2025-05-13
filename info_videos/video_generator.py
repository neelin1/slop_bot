import os
import numpy as np
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    CompositeAudioClip,
    ColorClip,
    concatenate_audioclips,
    AudioClip
)

def create_conversation_video(
    teacher1_image_path,
    teacher2_image_path,
    audio_conversation,
    content_image_paths,
    output_path="info_videos/assets/output/conversation_video.mp4",
    fps=24,
    height=1280,
    image_duration=10
):
    """
    Creates a video with two teachers having a conversation with fading effects.
    
    Args:
        teacher1_image_path (str): Path to the first teacher image
        teacher2_image_path (str): Path to the second teacher image
        audio_conversation (list): List of dictionaries with 'speaker', 'text', 'audio_path' keys
        content_image_paths (list): List of paths to content images
        output_path (str): Path to save the output video
        fps (int): Frames per second for the video
        height (int): Height of the video in pixels (9:16 portrait aspect ratio will be used)
        image_duration (int): Duration in seconds for each content image (default: 10)
        
    Returns:
        str: Path to the generated video
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # Width for video (9:16 portrait aspect ratio)
        video_width = int(height * 9 / 16)
        
        # Calculate teacher image size - make teachers smaller to fit in the portrait layout
        teacher_size = int(video_width * 0.4)  # Teacher image will be 40% of the width
        
        # Get first speaker name for reference
        teacher1_name = audio_conversation[0]["speaker"]
        
        # Prepare audio clips and gather durations
        audio_clips = []
        total_duration = 0
        segment_times = []  # Start and end times for each segment
        
        # Check if any segments have missing audio
        has_missing_audio = any(segment.get("audio_path") is None for segment in audio_conversation)
        if has_missing_audio:
            print("⚠️ Some audio segments are missing. Using silent audio for those parts.")
        
        for segment in audio_conversation:
            # Calculate duration for this segment
            if segment.get("audio_path") and os.path.exists(segment["audio_path"]):
                # Use the actual audio file
                audio_clip = AudioFileClip(segment["audio_path"])
                segment_duration = audio_clip.duration
            else:
                # Create silent audio based on text length (estimate 0.3 seconds per word)
                word_count = len(segment["text"].split())
                segment_duration = max(2.0, word_count * 0.3)  # At least 2 seconds
                print(f"  Creating {segment_duration:.1f}s silent audio for '{segment['text'][:30]}...'")
                
                # Create silent audio clip
                silent_audio = AudioClip(lambda t: 0, duration=segment_duration)
                audio_clip = silent_audio
            
            audio_clips.append(audio_clip)
            
            # Record segment timing information
            start_time = total_duration
            total_duration += segment_duration
            
            segment_times.append({
                "speaker": segment["speaker"],
                "text": segment["text"],
                "start": start_time,
                "end": total_duration,
                "has_audio": segment.get("audio_path") is not None
            })
        
        # Combine all audio clips
        if audio_clips:
            combined_audio = concatenate_audioclips(audio_clips)
        else:
            print("❌ No audio clips to combine.")
            return None
        
        # Create clips list
        clips = []
        
        # Add background content images (cycling through them if needed)
        current_time = 0
        image_index = 0
        while current_time < total_duration:
            # Cycle through available content images
            img_path = content_image_paths[image_index % len(content_image_paths)]
            image_index += 1
            
            # Determine duration for this content image (image_duration seconds or remaining time)
            img_duration = min(float(image_duration), total_duration - current_time)
            
            # Resize the content image to fit the top portion of the 9:16 video
            # Leave space at the bottom for teachers and text
            content_clip = (
                ImageClip(img_path)
                .set_start(current_time)
                .set_duration(img_duration)
                .resize(width=video_width)  # Resize to fit width
                .set_position(("center", int(height * 0.1)))  # Position at top with slight padding
            )
            clips.append(content_clip)
            current_time += img_duration
        
        # Load teacher images
        teacher1_img = ImageClip(teacher1_image_path)
        teacher2_img = ImageClip(teacher2_image_path)
        
        # Create clips for each teacher
        for segment in segment_times:
            # Determine which teacher is speaking
            is_teacher1 = (segment["speaker"] == teacher1_name)
            
            # Position coordinates for teachers in portrait mode
            # Position teachers side by side in the middle section of the video
            teacher1_pos = (int(video_width * 0.1), int(height * 0.45))  # Left side, middle section
            teacher2_pos = (int(video_width * 0.5), int(height * 0.45))  # Right side, middle section
            
            # Active teacher (speaking) - full opacity
            active_teacher_clip = (
                (teacher1_img if is_teacher1 else teacher2_img)
                .set_start(segment["start"])
                .set_duration(segment["end"] - segment["start"])
                .resize(height=teacher_size)
                .set_position(teacher1_pos if is_teacher1 else teacher2_pos)
            )
            
            # Inactive teacher - reduced opacity
            inactive_teacher_clip = (
                (teacher2_img if is_teacher1 else teacher1_img)
                .set_start(segment["start"])
                .set_duration(segment["end"] - segment["start"])
                .resize(height=teacher_size)
                .set_opacity(0.6)  # Reduced opacity for inactive teacher
                .set_position(teacher2_pos if is_teacher1 else teacher1_pos)
            )
            
            # Add both teachers to the clips
            clips.append(active_teacher_clip)
            clips.append(inactive_teacher_clip)
            
            # Add text clip for this segment at the bottom of the video
            text_bg_height = int(height * 0.2)  # 20% of height for text area
            
            # Text background spanning the width of the video
            available_width = int(video_width * 0.9)  # 90% of video width
            
            bg_clip = (
                ColorClip(
                    size=(available_width, text_bg_height),
                    color=(0, 0, 0)
                )
                .set_opacity(0.7)  # Slightly more opaque for better readability
                .set_position(("center", int(height * 0.75)))  # Position in bottom portion
                .set_start(segment["start"])
                .set_duration(segment["end"] - segment["start"])
            )
            clips.append(bg_clip)
            
            # Text for this segment - add a marker if this is using silent audio
            display_text = segment["text"]
            if not segment.get("has_audio", True):
                display_text = "[SILENT] " + display_text
            
            txt_clip = (
                TextClip(
                    display_text,
                    fontsize=30,
                    font="Arial-Bold",
                    color="white",
                    stroke_color="black",
                    stroke_width=1,
                    method="caption",
                    size=(available_width - 40, None)
                )
                .set_position(("center", int(height * 0.75)))  # Align with background
                .set_start(segment["start"])
                .set_duration(segment["end"] - segment["start"])
            )
            clips.append(txt_clip)
        
        # Create final composite video
        final_clip = CompositeVideoClip(clips, size=(video_width, height))
        final_clip = final_clip.set_audio(combined_audio)
        
        # Write video file
        final_clip.write_videofile(output_path, fps=fps, codec="libx264")
        
        return output_path
    
    except Exception as e:
        print(f"❌ Failed to create conversation video: {e}")
        return None

def create_info_video(
    teacher_image_path,
    content_image_paths,
    audio_path,
    text_segments,
    output_path="info_videos/assets/output/info_video.mp4",
    fps=24,
    height=1280,
    segment_duration=10
):
    """
    Creates an informational video with a teacher image and content images
    synchronized with the audio.
    
    Args:
        teacher_image_path (str): Path to the teacher image (with transparent background)
        content_image_paths (list): List of paths to content images
        audio_path (str): Path to the audio file
        text_segments (list): List of text segments corresponding to content images
        output_path (str): Path to save the output video
        fps (int): Frames per second for the video
        height (int): Height of the video in pixels (9:16 portrait aspect ratio will be used)
        segment_duration (int): Duration of each content segment in seconds
        
    Returns:
        str: Path to the generated video
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # Load audio clip to get total duration
        audio_clip = AudioFileClip(audio_path)
        total_duration = audio_clip.duration
        
        # Create clips for each segment
        clips = []
        
        # Calculate teacher image size for portrait mode
        teacher_size = int(height * 0.25)  # Teacher image will be 25% of the height
        
        # Width for video (9:16 portrait aspect ratio)
        video_width = int(height * 9 / 16)
        
        # Create content segments
        start_time = 0
        for i, (content_img_path, text_segment) in enumerate(zip(content_image_paths, text_segments)):
            # Determine segment duration (last segment might be shorter)
            if i == len(content_image_paths) - 1:
                duration = total_duration - start_time
            else:
                duration = min(segment_duration, total_duration - start_time)
            
            if duration <= 0:
                break
                
            # Create content image clip positioned in the top portion of the video
            content_clip = (
                ImageClip(content_img_path)
                .set_start(start_time)
                .set_duration(duration)
                .resize(width=video_width)
                .set_position(("center", int(height * 0.1)))  # Position at top with padding
            )
            
            # Append content clip first (lowest layer)
            clips.append(content_clip)
            
            start_time += duration
        
        # Load teacher image as clip (middle layer) at the bottom center of the video
        teacher_clip = (
            ImageClip(teacher_image_path)
            .set_duration(total_duration)
            .resize(height=teacher_size)
            .set_position(("center", int(height * 0.5)))  # Position in middle section
        )
        clips.append(teacher_clip)
        
        # Create text segments (top layer, in front of everything including teacher)
        start_time = 0
        for i, text_segment in enumerate(text_segments):
            # Determine segment duration
            if i == len(text_segments) - 1:
                duration = total_duration - start_time
            else:
                duration = min(segment_duration, total_duration - start_time)
            
            if duration <= 0 or not text_segment:
                start_time += duration
                continue
                
            # Calculate text width to match content image area
            available_width = int(video_width * 0.9)  # 90% of video width
                
            # Create a semi-transparent black background for text at the bottom of the video
            text_bg_height = int(height * 0.2)  # 20% of height for text
            bg_clip = (
                ColorClip(
                    size=(available_width, text_bg_height),
                    color=(0, 0, 0)
                )
                .set_opacity(0.7)  # Make it semi-transparent
                .set_position(("center", int(height * 0.75)))  # Position in bottom portion
                .set_start(start_time)
                .set_duration(duration)
            )
            clips.append(bg_clip)
            
            # Create text clip on top of the background
            txt_clip = (
                TextClip(
                    text_segment,
                    fontsize=30,
                    font="Arial-Bold",
                    color="white",
                    stroke_color="black",
                    stroke_width=1,
                    method="caption",
                    size=(available_width - 40, None)
                )
                .set_position(("center", int(height * 0.75)))  # Align with background
                .set_start(start_time)
                .set_duration(duration)
            )
            clips.append(txt_clip)
            
            start_time += duration
        
        # Create final composite clip
        final_clip = CompositeVideoClip(clips, size=(video_width, height))
        final_clip = final_clip.set_audio(audio_clip)
        
        # Write video file
        final_clip.write_videofile(output_path, fps=fps, codec="libx264")
        
        return output_path
    
    except Exception as e:
        print(f"❌ Failed to create video: {e}")
        return None 