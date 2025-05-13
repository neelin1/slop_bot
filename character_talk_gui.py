#!/usr/bin/env python3
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import re
from PIL import Image, ImageTk
from info_videos.main import generate_conversation_video
from info_videos.image_generator import get_topic_collection

class CharacterConversationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Character Conversation Generator")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Set theme
        style = ttk.Style()
        style.theme_use('clam')  # Using 'clam' theme which looks good across platforms
        
        # UI elements
        self.create_widgets()
        
        # Known characters
        self.known_characters = [
            "Peter Griffin", "Quagmire", "Homer Simpson", "Bart Simpson", 
            "Stewie Griffin", "Wendy from Wendy's", "Ronald McDonald", "Mickey Mouse", 
            "Donald Duck", "Cercei Lannister", "John Pork"
        ]
        
        # Add known characters to dropdown menus
        self.char1_dropdown['values'] = self.known_characters
        self.char2_dropdown['values'] = self.known_characters
        
        # Default characters
        self.char1_dropdown.set("Wendy from Wendy's")
        self.char2_dropdown.set("Ronald McDonald")
        
        # Define example prompts
        self.example_prompts = [
            "the politics of Indonesia",
            "how to cook pasta",
            "quantum physics theories",
            "climate change and its impacts",
            "the history of video games"
        ]
        
        # Add example prompts to the dropdown menu
        self.example_prompt_var.set("Choose an example topic...")
        self.example_prompt_dropdown['values'] = self.example_prompts
        
        # Output directory
        self.output_dir = "info_videos/assets/output"
        os.makedirs(self.output_dir, exist_ok=True)

    def create_widgets(self):
        # Create a main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title label
        title_label = ttk.Label(main_frame, text="Generate Character Conversations", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="w")
        
        # Character selection
        ttk.Label(main_frame, text="Character 1:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", pady=5)
        self.char1_var = tk.StringVar()
        self.char1_dropdown = ttk.Combobox(main_frame, textvariable=self.char1_var, width=25, font=("Arial", 12))
        self.char1_dropdown.grid(row=1, column=1, sticky="w", pady=5)
        
        ttk.Label(main_frame, text="Character 2:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", pady=5)
        self.char2_var = tk.StringVar()
        self.char2_dropdown = ttk.Combobox(main_frame, textvariable=self.char2_var, width=25, font=("Arial", 12))
        self.char2_dropdown.grid(row=2, column=1, sticky="w", pady=5)
        
        # Topic entry
        ttk.Label(main_frame, text="Topic:", font=("Arial", 12)).grid(row=3, column=0, sticky="w", pady=5)
        self.topic_var = tk.StringVar()
        self.topic_entry = ttk.Entry(main_frame, textvariable=self.topic_var, width=40, font=("Arial", 12))
        self.topic_entry.grid(row=3, column=1, columnspan=2, sticky="we", pady=5)
        
        # Example prompts
        ttk.Label(main_frame, text="Example topics:", font=("Arial", 12)).grid(row=4, column=0, sticky="w", pady=5)
        self.example_prompt_var = tk.StringVar()
        self.example_prompt_dropdown = ttk.Combobox(main_frame, textvariable=self.example_prompt_var, width=40, font=("Arial", 12))
        self.example_prompt_dropdown.grid(row=4, column=1, columnspan=2, sticky="we", pady=5)
        self.example_prompt_dropdown.bind("<<ComboboxSelected>>", self.use_example_prompt)
        
        # Speech speed
        ttk.Label(main_frame, text="Speech Speed:", font=("Arial", 12)).grid(row=5, column=0, sticky="w", pady=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = ttk.Scale(main_frame, variable=self.speed_var, from_=0.5, to=1.5, length=200, orient="horizontal")
        self.speed_scale.grid(row=5, column=1, sticky="w", pady=5)
        ttk.Label(main_frame, textvariable=self.speed_var).grid(row=5, column=2, sticky="w", pady=5)
        
        # Duration slider
        ttk.Label(main_frame, text="Duration (seconds):", font=("Arial", 12)).grid(row=6, column=0, sticky="w", pady=5)
        self.duration_var = tk.IntVar(value=30)
        self.duration_scale = ttk.Scale(main_frame, variable=self.duration_var, from_=10, to=120, length=200, orient="horizontal")
        self.duration_scale.grid(row=6, column=1, sticky="w", pady=5)
        ttk.Label(main_frame, textvariable=self.duration_var).grid(row=6, column=2, sticky="w", pady=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=7, column=0, columnspan=3, sticky="we", pady=10)
        
        self.progress = ttk.Progressbar(progress_frame, orient="horizontal", length=700, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=5)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var, font=("Arial", 10))
        status_label.pack(fill=tk.X, pady=5)
        
        # Output path
        self.output_path_var = tk.StringVar()
        output_path_frame = ttk.Frame(progress_frame)
        output_path_frame.pack(fill=tk.X, pady=5)
        ttk.Label(output_path_frame, text="Output:", font=("Arial", 10)).pack(side=tk.LEFT)
        ttk.Label(output_path_frame, textvariable=self.output_path_var, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=3, pady=10)
        
        self.generate_button = ttk.Button(button_frame, text="Generate Conversation", command=self.generate)
        self.generate_button.pack(side=tk.LEFT, padx=5)
        
        self.play_button = ttk.Button(button_frame, text="Play Video", command=self.play_video, state=tk.DISABLED)
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.open_folder_button = ttk.Button(button_frame, text="Open Output Folder", command=self.open_output_folder)
        self.open_folder_button.pack(side=tk.LEFT, padx=5)
        
        # Configure grid column weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)

    def use_example_prompt(self, event):
        if self.example_prompt_var.get() != "Choose an example topic...":
            self.topic_var.set(self.example_prompt_var.get())
    
    def generate(self):
        # Get character and topic
        character1 = self.char1_var.get()
        if not character1:
            messagebox.showerror("Error", "Please select Character 1")
            return
            
        character2 = self.char2_var.get()
        if not character2:
            messagebox.showerror("Error", "Please select Character 2")
            return
            
        topic = self.topic_var.get()
        if not topic:
            messagebox.showerror("Error", "Please enter a topic")
            return
        
        # Try to parse the topic field in case it contains a full prompt
        # like "Character1 talking to Character2 about Topic"
        import re
        
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
        
        # Check if any common conversation pattern is in the topic
        if any(keyword in topic.lower() for keyword in ['talking', 'speaking', 'discussing', 'debating', 'arguing']):
            # Pattern 1: "X talking to Y about Z"
            talk_pattern = re.compile(f'(.*?)\\s+{conversation_keywords}\\s+{relation_words}\\s+(.*?)\\s+about\\s+(.*)', re.IGNORECASE)
            match = talk_pattern.match(topic)
            
            # Pattern 2: "X and Y discussing Z"
            if not match:
                joint_pattern = re.compile(r'(.*?)\s+and\s+(.*?)\s+(?:discussing|talking about|debating|arguing about)\s+(.*)', re.IGNORECASE)
                match = joint_pattern.match(topic)
                
            # Pattern 3: "X vs Y on the topic of Z"
            if not match:
                versus_pattern = re.compile(r'(.*?)\s+(?:vs|versus|against|opposing)\s+(.*?)\s+(?:on|about|regarding|concerning|discussing)\s+(.*)', re.IGNORECASE)
                match = versus_pattern.match(topic)
            
            if match:
                # Extract the characters and topic
                character1 = match.group(1).strip().title()
                character2 = match.group(2).strip().title()
                topic = match.group(3).strip()
                
                # Update the UI fields
                self.char1_var.set(character1)
                self.char2_var.set(character2)
                self.topic_var.set(topic)
                
                # Let the user know their prompt was parsed
                self.status_var.set(f"Extracted: {character1} and {character2} discussing {topic}")
        
        # Disable inputs during generation
        self.generate_button.config(state=tk.DISABLED)
        self.play_button.config(state=tk.DISABLED)
        self.char1_dropdown.config(state=tk.DISABLED)
        self.char2_dropdown.config(state=tk.DISABLED)
        self.topic_entry.config(state=tk.DISABLED)
        self.example_prompt_dropdown.config(state=tk.DISABLED)
        self.speed_scale.config(state=tk.DISABLED)
        self.duration_scale.config(state=tk.DISABLED)
        
        # Start progress bar
        self.progress.start()
        self.status_var.set("Starting generation...")
        
        # Run generation in a background thread
        generation_thread = threading.Thread(
            target=self.generate_video_thread,
            args=(character1, character2, topic, self.speed_var.get(), self.duration_var.get())
        )
        generation_thread.daemon = True
        generation_thread.start()
    
    def generate_video_thread(self, character1, character2, topic, speech_speed, duration_seconds):
        try:
            # Clean up any existing character images
            self.status_var.set("Cleaning up existing character images...")
            teachers_dir = "info_videos/assets/teachers"
            if os.path.exists(teachers_dir):
                for filename in os.listdir(teachers_dir):
                    if character1.split()[0].lower() in filename.lower() or character2.split()[0].lower() in filename.lower():
                        file_path = os.path.join(teachers_dir, filename)
                        try:
                            os.remove(file_path)
                        except:
                            pass
            
            # Generate image topics
            self.status_var.set("Generating image topics...")
            
            # Calculate how many images we need based on duration (roughly 1 image per 10 seconds)
            num_images = max(1, min(12, duration_seconds // 10))
            
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
            
            # Select voices
            self.status_var.set("Selecting voices for characters...")
            char1_voice, char1_pitch, char1_style, char1_speed = self.select_voice(character1)
            char2_voice, char2_pitch, char2_style, char2_speed = self.select_voice(character2)
            
            # Generate output path
            char1_name = character1.split()[0]
            char2_name = character2.split()[0]
            topic_short = re.sub(r'[^\w\s]', '', topic).replace(' ', '_')[:20]
            output_path = os.path.join(self.output_dir, f"{char1_name}_{char2_name}_{topic_short}.mp4")
            
            # Update status with summary
            self.status_var.set(f"Generating conversation between {character1} and {character2} about '{topic}'...")
            
            # Generate a longer input text for the conversation based on the desired duration
            # Calculate word count based on desired duration - aim for more words than needed
            # to ensure the conversation is long enough
            target_word_count = duration_seconds * 3  # Approximately 3 words per second
            
            # Create a more detailed prompt that explicitly states the number of exchanges needed
            # The number of exchanges should be at least the number of images to ensure all images are used
            min_exchanges = max(4, len(image_topics))
            
            enhanced_topic = (
                f"Create a conversation between {character1} and {character2} discussing: {topic}. "
                f"The conversation should be EXACTLY {duration_seconds} seconds long when read aloud, "
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
                input_text=enhanced_topic,
                output_path=output_path,
                speech_speed=speech_speed,
                # Use the selected voices
                teacher1_voice=char1_voice,
                teacher2_voice=char2_voice,
                teacher1_pitch=char1_pitch,
                teacher2_pitch=char2_pitch,
                teacher1_style=char1_style,
                teacher2_style=char2_style,
                teacher1_speed=char1_speed,
                teacher2_speed=char2_speed,
                # Use images
                image_topics=image_topics,
                # Set image duration based on total duration and number of images
                image_duration=max(5, min(15, duration_seconds // len(image_topics)))
            )
            
            # Update UI on the main thread
            self.root.after(0, self.generation_complete, video_path)
            
        except Exception as e:
            # Handle errors
            self.root.after(0, self.generation_error, str(e))
    
    def select_voice(self, char_name):
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
    
    def generation_complete(self, video_path):
        # Stop progress bar
        self.progress.stop()
        
        if video_path:
            # Update status and output path
            self.status_var.set("Generation complete! ✅")
            self.output_path_var.set(video_path)
            
            # Enable play button
            self.play_button.config(state=tk.NORMAL)
            
            # Show success message
            messagebox.showinfo("Success", f"Conversation video generated successfully!\n\nFile: {video_path}")
        else:
            # Show error
            self.status_var.set("Generation failed ❌")
            messagebox.showerror("Error", "Failed to generate conversation video")
        
        # Re-enable inputs
        self.generate_button.config(state=tk.NORMAL)
        self.char1_dropdown.config(state=tk.NORMAL)
        self.char2_dropdown.config(state=tk.NORMAL)
        self.topic_entry.config(state=tk.NORMAL)
        self.example_prompt_dropdown.config(state=tk.NORMAL)
        self.speed_scale.config(state=tk.NORMAL)
        self.duration_scale.config(state=tk.NORMAL)
    
    def generation_error(self, error_message):
        # Stop progress bar
        self.progress.stop()
        
        # Update status
        self.status_var.set(f"Error: {error_message}")
        
        # Show error message
        messagebox.showerror("Error", f"An error occurred during generation:\n\n{error_message}")
        
        # Re-enable inputs
        self.generate_button.config(state=tk.NORMAL)
        self.char1_dropdown.config(state=tk.NORMAL)
        self.char2_dropdown.config(state=tk.NORMAL)
        self.topic_entry.config(state=tk.NORMAL)
        self.example_prompt_dropdown.config(state=tk.NORMAL)
        self.speed_scale.config(state=tk.NORMAL)
        self.duration_scale.config(state=tk.NORMAL)
    
    def play_video(self):
        video_path = self.output_path_var.get()
        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("Error", "Video file not found")
            return
        
        # Open video with default player
        import subprocess
        import platform
        
        system = platform.system()
        try:
            if system == 'Darwin':  # macOS
                subprocess.call(('open', video_path))
            elif system == 'Windows':
                os.startfile(video_path)
            else:  # Linux
                subprocess.call(('xdg-open', video_path))
        except Exception as e:
            messagebox.showerror("Error", f"Could not open video: {str(e)}")
    
    def open_output_folder(self):
        # Open the output folder in file explorer
        import subprocess
        import platform
        
        system = platform.system()
        try:
            if system == 'Darwin':  # macOS
                subprocess.call(('open', self.output_dir))
            elif system == 'Windows':
                os.startfile(self.output_dir)
            else:  # Linux
                subprocess.call(('xdg-open', self.output_dir))
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {str(e)}")

def main():
    root = tk.Tk()
    app = CharacterConversationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 