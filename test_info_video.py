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
    
    # Generate an informational video with Peter Griffin as the teacher
    video_path = generate_info_video(
        teacher_name="Peter Griffin",
        input_text=educational_content,
        output_path="info_videos/assets/output/climate_change_video.mp4"
    )
    
    if video_path:
        print(f"\n✅ Test successful! Video generated at: {video_path}")
    else:
        print("\n❌ Test failed! Unable to generate video.")

if __name__ == "__main__":
    main() 