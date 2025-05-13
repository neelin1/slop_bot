#!/usr/bin/env python3
from info_videos.main import generate_info_video

def main():
    # Sample educational content text
    educational_content = (
        "Climate change is the long-term alteration of temperature and typical weather patterns. "
        "This change has been primarily caused by human activities, particularly the burning of fossil fuels, "
        "which releases greenhouse gases into the atmosphere. These gases trap heat and lead to global warming. "
        "Effects of climate change include rising sea levels, more frequent extreme weather events, and disruptions to ecosystems."
    )
    
    # Generate an informational video with a professional teacher, faster speech, and text in front of teacher
    video_path = generate_info_video(
        teacher_name="Professor Sarah Johnson",
        input_text=educational_content,
        output_path="info_videos/assets/output/faster_text_in_front_video.mp4",
        speech_speed=1.5  # 50% faster speech
    )
    
    if video_path:
        print(f"\n✅ Test successful! Updated video (faster speech, text in front) generated at: {video_path}")
    else:
        print("\n❌ Test failed! Unable to generate updated video.")

if __name__ == "__main__":
    main() 