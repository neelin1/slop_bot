story: str = """
The pupil looked back at the chalkboard, squinting to try and garner any deeper meaning to the neatly written message.

Humility

The word lay printed in large block letters for the entire classroom to see, the Archmage standing in front of her handiwork as if the meaning could not be more apparent.

“Then explain yourself,” the pupil demanded, murmurs of agreement around him. “You speak as if you have just revealed the grand design of the universe but seem more prepared to teach us a childish lesson of nursery rhymes. Humility? We seek power, you of all people should know that.”

The Archmage nodded along, the small smile adorning her wrinkled face never breaking.

“And how will you wield this power?”

The pupil stared back, brow furrowing. This was getting tiresome.

“That is what we are here to learn – how to draw power from ourselves.” He clenched his quill, the stem flexing. “To command the elements, to laugh in the face of psychics, to bend the wills of the universe to our desires. What all great mages seek.”

“And you think I am here to grant you those answers?”

“Oh, enough of your questions!” The pupil’s temper flared, the atmosphere in the room thickening. “Tell us then, how does humility teach us to command power?”

The Archmage’s calm demeanor remained unaffected by the outburst. There was always one in each class. She took a step toward the pupil, who shrunk back into their chair.

“There are laws of the universe. You yourself have stated as such.” She began. “Laws that have helped life form, helped societies rise and fall. Call them the laws of physics, thermodynamics, whatever you may. Tell me, what happens to a structure, construct or living, if gravity increases just 1 meter per second for half a second?”

The pupil lay silent. They were a wizard, not a mathematician.

“Total structural collapse.” The Archmage continued. “They were designed according to the laws that this world operates under. Any changes to those lead to constants being converted into variables. And from there, unpredictability.”

The pupil looked back, waiting for the Archmage to continue. But she remained silent, the room still as her words sunk around here.

“And?” the pupil asked cautiously.

The Archmage sighed.

“I was hoping the rest should be obvious. When we dabble in magic, we are altering perfect rules, rules that have constructed what we know as existence. That is why humility is the true secret ever apprentice must first master - knowing how and why the rules we are breaking exist and ensuring we do not bring an end to the fabric of existence as we know it.”

The class stared back at the old woman. Each and everyone in the room was there to seek power. But how simple would it be for them to cast their egos aside in pursuit of this mastery?

Could humility truly be taught, or was it something that had to be broken into a soul, like a wild beast learning how to please its master?

The Archmage had been over this lesson time and time again with newer and younger cohorts, and even she was unsure of that answer.
"""


input_parameters = {
    "story": story,
    "director_prompt": "Fantasy dark academia, oil painting style",  # optional parameter
    "video_gen": False,  # optional parameter, defaults to False, if True, will generate videos, otherwise images with pans
    "music": False,  # optional parameter, defaults to False, if True, will generate music, otherwise will use a default background track, if true need anotehr parameter  (file name of music)
    # character design: str, optional parameter that will be inputted to high-level plan
}

# High-level plan
# generates a single string describing the video
# visual style, visual flow, character design, what will be shown in major scenes, etc.

# Thing extractor
# extract any major items the story that should have visual consistency, i.e. characters, locations, groups, etc.
# [ { name: str, description:str }, ...]

# Scene-bot
# generates a list of scenes (iterative multi-turn, each turn generates up to 4 new scenes)
# [ { text: str (original text from story covered by this image), desription: str (detailed prompt for image generation)}, ...]

# guardrails
# ensures the text corresponds to the original story (gpt call, doesnt need exact match, but should be close), if fails will replace or add scenes to list

# image generation
# generate a list of images based on the text using 4o api

# audio generation
# generate a list of audio clips based on the text

# video generation
# 2 options:
# generate videos using sora
# generate videos using pans
# post-processing to add test

# post-processing
# merge videos and audio to create final product
# music
