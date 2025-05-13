# Character Conversation Generator

Generate fun and engaging conversation videos between fictional characters on any topic!

## Features

- Create conversations between any characters you can imagine - no limitations!
- Generate AI-produced images relevant to the conversation topic
- Customize video duration from 10 seconds up to 2 minutes
- Adjust speech speed for natural-sounding conversations
- Automatically selects appropriate voices and speech characteristics for characters
- Available as both a command-line tool and a user-friendly GUI

## Installation

Ensure you have the required dependencies installed:

```bash
pip install -r requirements.txt
```

## Usage

### Command-Line Interface

```bash
python character_talk.py --prompt "Peter Griffin talking to Quagmire about the politics of Indonesia"
```

Options:
- `--prompt`: The conversation prompt. Ideally in the format "Character1 talking to Character2 about Topic"
- `--speech-speed`: (Optional) Speed of speech (default: 1.0)
- `--duration`: (Optional) Target duration in seconds (default: 30, max recommended: 120)

Examples:
```bash
# Generate a 60-second conversation between Peter and Homer
python character_talk.py --prompt "Peter Griffin talking to Homer Simpson about climate change" --duration 60

# Create a quick 20-second exchange with faster speech
python character_talk.py --prompt "Stewie talking to Bart about pranks" --duration 20 --speech-speed 1.2

# Use any characters you can imagine
python character_talk.py --prompt "A Neanderthal talking to a Robot about modern technology" --duration 40
python character_talk.py --prompt "Elderly Dragon talking to Baby Elephant about the meaning of life" --duration 60
```

### Graphical User Interface

For a more user-friendly experience, run:

```bash
python character_talk_gui.py
```

The GUI allows you to:
1. Enter any characters you want for the conversation
2. Enter a conversation topic
3. Choose from example topics
4. Adjust speech speed
5. Set the desired video duration (10-120 seconds)
6. Generate and play the video

## Character Voice Selection

The system intelligently selects appropriate voices for any character:

- **Known Characters**: Predefined voices for popular characters like Peter Griffin, Wendy, etc.
- **Custom Characters**: Automatically analyzes the character description to select appropriate voices:
  - Gender-based selection (male/female voices)
  - Age-appropriate pitch adjustments (child, adult, elderly)
  - Character-type specific voices (monsters, robots, animals, etc.)

Examples of how custom character voices are selected:
- "Elderly Woman" → Female voice with lower pitch
- "Robot" → Male voice with mechanical tone
- "Baby Girl" → Female voice with higher pitch
- "Dragon" → Deep, monstrous voice
- "Small Dog" → Higher-pitched animal voice

## How Duration Affects Videos

The duration parameter affects several aspects of the generated video:

- **Content Length**: Longer durations produce more detailed conversations with more in-depth discussion
- **Number of Images**: The system automatically calculates how many topic images to use (approximately 1 per 10 seconds)
- **Image Display Time**: Each image is shown for an appropriate duration based on the total video length
- **Exchange Count**: Longer durations automatically create more back-and-forth exchanges between characters

The generator uses advanced prompting to ensure that conversations actually match the requested duration, with:
- Precise word count calculation based on the target duration
- Minimum number of exchanges that scales with video length
- Specific instructions to maintain character personalities and natural dialogue
- Balanced speaking time between characters

For optimal results:
- 10-30 seconds: Quick exchanges, good for simple topics
- 30-60 seconds: Balanced conversations with moderate detail
- 60-120 seconds: In-depth discussions with multiple subtopics

## Output

Videos are saved in `info_videos/assets/output/` with filenames based on the characters and topic.

## Examples

1. `python character_talk.py --prompt "Peter Griffin talking to Homer Simpson about climate change" --duration 60`
2. `python character_talk.py --prompt "Wendy from Wendy's talking to Ronald McDonald about fast food competition" --duration 45`
3. `python character_talk.py --prompt "Stewie Griffin talking to Bart Simpson about school pranks" --duration 30`
4. `python character_talk.py --prompt "Neanderthal talking to Robot about smartphones" --duration 45`
5. `python character_talk.py --prompt "Wise Old Turtle talking to Young Eagle about flying" --duration 60`

## Notes

- Character images are generated on first use and cached for future use
- Each video includes topic-relevant images based on the requested duration
- Longer videos automatically generate more detailed conversation prompts 