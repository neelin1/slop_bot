# Character Talk Video Generator

## Building and Running the Tool

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/slop_bot.git
cd slop_bot
```

### Step 2: Set Up Python Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Set Up API Keys

Create a `.env` file in the project root with your API keys:

```
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### Step 4: Run the Tool

Here's the usage example:

```bash
python info_videos/character_talk.py --pdf info_videos/sample_pdfs/dartboard.pdf --prompt "Eric Cartman talking to Homer Simpson" --duration 90 --custom-images info_videos/sample_images/dartboard_paper.png info_videos/sample_images/dartboard.webp info_videos/sample_images/darts.png
```

Or use the GUI version:

```bash
python info_videos/character_talk_gui.py
```

## Overview

This tool generates entertaining videos with animated character conversations in portrait mode (9:16 aspect ratio), perfect for social media platforms like TikTok and Instagram Reels. It features:

- FakeYou text-to-speech integration for authentic character voices
- Automatic script generation based on your prompt
- Dynamic character positioning and animations
- Support for custom images and educational content

## Prerequisites

Before running the tool, make sure you have:

1. Python 3.8+ installed
2. Required Python packages (install via `pip install -r requirements.txt`)
3. API keys for OpenAI and Google Imagen (for content and image generation)

## Command Line Options

- `--prompt`: Describe the conversation (required unless using `--pdf`)
- `--duration`: Target video duration in seconds (default: 30, max recommended: 120)
- `--speech-speed`: Speed of speech (default: 1.0)
- `--no-fallback`: Disable fallback voices when FakeYou fails
- `--summary-mode`: Generate summarized content instead of detailed technical content

## Troubleshooting

### API Connection Issues

If the command hangs without output, check:

1. Your API keys are correctly set in the `.env` file
2. You have internet connectivity
3. The API services are not rate-limiting your requests

### Missing Audio

If characters are silent in the output video:

1. Try using the `--no-fallback` option to see if there are API errors
2. Check if FakeYou service is available

### Other Issues

- If generating long videos, try reducing the `--duration` parameter
- For clearer audio, adjust the `--speech-speed` parameter

## Advanced Configuration

For advanced users, you can modify character voice tokens in `info_videos/fakeyou_audio.py` to add support for more characters. 