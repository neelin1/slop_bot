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
    concatenate_audioclips
)

def create_conversation_video(
    teacher1_image_path,
    teacher2_image_path,
    audio_conversation,
    content_image_paths,
    output_path="info_videos/assets/output/conversation_video.mp4",
    fps=24,
    height=720,
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
        height (int): Height of the video in pixels
        image_duration (int): Duration in seconds for each content image (default: 10)
        
    Returns:
        str: Path to the generated video
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # Width for video (16:9 aspect ratio)
        video_width = int(height * 16 / 9)
        
        # Calculate teacher image size - make teachers larger (1/2 of height instead of 1/3)
        teacher_size = height // 2  # Teacher image will be 1/2 of the height
        
        # Get first speaker name for reference
        teacher1_name = audio_conversation[0]["speaker"]
        
        # Prepare audio clips and gather durations
        audio_clips = []
        total_duration = 0
        segment_times = []  # Start and end times for each segment
        
        for segment in audio_conversation:
            audio_clip = AudioFileClip(segment["audio_path"])
            audio_clips.append(audio_clip)
            
            start_time = total_duration
            total_duration += audio_clip.duration
            
            segment_times.append({
                "speaker": segment["speaker"],
                "text": segment["text"],
                "start": start_time,
                "end": total_duration
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
            
            content_clip = (
                ImageClip(img_path)
                .set_start(current_time)
                .set_duration(img_duration)
                .resize(height=height)
                .set_position("center")
            )
            clips.append(content_clip)
            current_time += img_duration
        
        # Create teacher clips with fade effects based on who's speaking
        # Load teacher images
        teacher1_img = ImageClip(teacher1_image_path)
        teacher2_img = ImageClip(teacher2_image_path)
        
        # Create clips for each teacher
        for segment in segment_times:
            # Determine which teacher is speaking
            is_teacher1 = (segment["speaker"] == teacher1_name)
            
            # Active teacher (speaking) - full opacity
            active_teacher_clip = (
                (teacher1_img if is_teacher1 else teacher2_img)
                .set_start(segment["start"])
                .set_duration(segment["end"] - segment["start"])
                .resize(height=teacher_size)
                .set_position(("left" if is_teacher1 else "right", "bottom"))
            )
            
            # Only add the active teacher - completely remove inactive teacher
            clips.append(active_teacher_clip)
            
            # Add text clip for this segment
            text_bg_height = height // 6
            
            # Calculate text width to match content image area, leaving space for teachers on both sides
            available_width = int(video_width * 0.7)  # 70% of video width
            
            bg_clip = (
                ColorClip(
                    size=(available_width, text_bg_height),
                    color=(0, 0, 0)
                )
                .set_opacity(0.6)
                .set_position(("center", "bottom"))
                .set_start(segment["start"])
                .set_duration(segment["end"] - segment["start"])
            )
            clips.append(bg_clip)
            
            # Text for this segment
            txt_clip = (
                TextClip(
                    segment["text"],
                    fontsize=30,
                    font="Arial-Bold",
                    color="white",
                    stroke_color="black",
                    stroke_width=1,
                    method="caption",
                    size=(available_width - 40, None)
                )
                .set_position(("center", "bottom"))
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
    height=720,
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
        height (int): Height of the video in pixels
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
        
        # Calculate teacher image size and position (larger, in corner)
        teacher_size = height // 2  # Teacher image will be 1/2 of the height (increased from 1/3)
        
        # Width for text background (16:9 aspect ratio)
        video_width = int(height * 16 / 9)
        
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
                
            # Create content image clip
            content_clip = (
                ImageClip(content_img_path)
                .set_start(start_time)
                .set_duration(duration)
                .resize(height=height)
                .set_position("center")
            )
            
            # Append content clip first (lowest layer)
            clips.append(content_clip)
            
            start_time += duration
        
        # Load teacher image as clip (middle layer)
        teacher_clip = (
            ImageClip(teacher_image_path)
            .set_duration(total_duration)
            .resize(height=teacher_size)
            .set_position(("right", "bottom"))
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
            # Subtract space for the teacher (about 1/3 of video width)
            available_width = int(video_width * 0.75)
                
            # Create a semi-transparent black background for text
            text_bg_height = height // 6  # Height of the text background
            bg_clip = (
                ColorClip(
                    size=(available_width, text_bg_height),
                    color=(0, 0, 0)
                )
                .set_opacity(0.6)  # Make it semi-transparent
                .set_position(("center", "bottom"))
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
                .set_position(("center", "bottom"))
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