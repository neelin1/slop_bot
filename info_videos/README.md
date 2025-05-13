# Informational Video Generator

This module generates informational videos with virtual teachers presenting educational content. It supports both single teacher presentations and conversations between two teachers.

## Features

### Single Teacher Mode:
- Generate a teacher image with transparent background
- Convert educational text into professional script
- Generate text-to-speech audio
- Create relevant content images for each segment
- Combine everything into a polished video

### Conversation Mode:
- Generate images for two teachers with transparent backgrounds
- Create natural conversation script between the teachers
- Use different voices for each teacher
- Fade inactive teacher into the background while the other is speaking
- Generate images relevant to the conversation
- Place text in front of the teachers

## Dependencies

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Note: This module requires the `rembg` package for background removal and `moviepy` for video creation. Also, ensure you have ImageMagick installed for text rendering in videos.

## Usage

### From Command Line

#### Single Teacher Mode

```bash
python -m info_videos.main --mode single --teacher "Professor Sarah Johnson" --input "The mitochondria is the powerhouse of the cell..." --output "my_video.mp4" --speed 1.3
```

#### Conversation Mode

```bash
python -m info_videos.main --mode conversation --teacher1 "Professor Sarah" --teacher2 "Professor Michael" --input "The mitochondria is the powerhouse of the cell..." --output "conversation.mp4" --speed 1.3
```

You can also provide a text file as input:

```bash
python -m info_videos.main --mode conversation --teacher1 "Professor Sarah" --teacher2 "Professor Michael" --input input_text.txt
```

### From Python Code

#### Single Teacher Mode

```python
from info_videos.main import generate_info_video

# Generate video with a single teacher explaining a topic
generate_info_video(
    teacher_name="Professor Sarah Johnson", 
    input_text="The mitochondria is the powerhouse of the cell...",
    output_path="my_video.mp4",
    speech_speed=1.3
)
```

#### Conversation Mode

```python
from info_videos.main import generate_conversation_video

# Generate video with two teachers discussing a topic
generate_conversation_video(
    teacher1_name="Professor Sarah",
    teacher2_name="Professor Michael",
    input_text="The mitochondria is the powerhouse of the cell...",
    output_path="conversation.mp4",
    speech_speed=1.3
)
```

## Output

The module will generate:
- Teacher images (with and without background)
- Content images for each segment or conversation exchange
- Audio files with the narration
- Final video with all elements combined

Output files are saved in the `info_videos/assets/` directory by default. 