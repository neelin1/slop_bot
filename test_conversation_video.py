#!/usr/bin/env python3
from info_videos.main import generate_conversation_video
from info_videos.image_generator import get_topic_collection

def main():
    educational_content = (
      "The citric acid cycle, also known as the Krebs cycle, is a central topic in Biochemistry II that illustrates how cells extract energy from nutrients. "
"In this cycle, acetyl-CoA—derived from carbohydrates, fats, and proteins—is oxidized to carbon dioxide in a series of enzyme-catalyzed steps. "
"Along the way, high-energy electron carriers like NADH and FADH₂ are produced, which later fuel ATP synthesis in the electron transport chain. "
"The cycle also generates GTP (or ATP), and key intermediates that serve as precursors for amino acids and other biosynthetic pathways. "
"Regulation of the cycle is tightly controlled through feedback inhibition and the availability of substrates and cofactors. "
"The citric acid cycle doesn’t operate in isolation—it integrates with glycolysis, fatty acid oxidation, and amino acid catabolism. "
"Disruptions in this cycle, such as enzyme deficiencies or mitochondrial dysfunction, can impair energy production and lead to metabolic diseases."
    )
    
    import os
    import shutil
    
    teachers_dir = "info_videos/assets/teachers"
    if os.path.exists(teachers_dir):
        for filename in os.listdir(teachers_dir):
            if "Cercei_Lannister" in filename or "John_Pork" in filename:
                file_path = os.path.join(teachers_dir, filename)
                os.remove(file_path)
                print(f"Removed existing file: {file_path}")
    
    nutrition_topics = get_topic_collection("The citric acid cycle")
    
    video_path = generate_conversation_video(
        teacher1_name="Wendy from Wendy's Fast Food Resturant",
        teacher2_name="Ronald McDonald from McDonald's",
        input_text=educational_content,
        output_path="info_videos/assets/output/nutrition_conversation.mp4",
        speech_speed=1.0,             
        teacher1_voice="alloy",        
        teacher2_voice="fable",        
        teacher1_pitch=-3,             
        teacher2_pitch=-2,                 
        teacher1_speed=1.0,            
        teacher2_speed=1.0,            
        image_topics=nutrition_topics  
    )
    
    if video_path:
        print(f"\n✅ Test successful! Conversation video generated at: {video_path}")
    else:
        print("\n❌ Test failed! Unable to generate conversation video.")

if __name__ == "__main__":
    main() 