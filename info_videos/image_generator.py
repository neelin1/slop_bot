import os
from PIL import Image
from io import BytesIO
import numpy as np
from rembg import remove
from slop_gen.utils.api_utils import generate_images_with_imagen

def is_fictional_character(name):
    """
    Check if the name matches known fictional characters to use special prompts.
    
    Args:
        name (str): Character name to check
        
    Returns:
        bool: True if it's a fictional character, False otherwise
    """
    fictional_characters = {
        "peter griffin": "animated character from Family Guy, cartoon style",
        "stewie griffin": "infant character from Family Guy with football-shaped head, cartoon style",
        "stewie": "infant character from Family Guy with football-shaped head, cartoon style",
        "homer simpson": "yellow cartoon character from The Simpsons",
        "bart simpson": "yellow cartoon character with spiky hair from The Simpsons",
        "mickey mouse": "Disney cartoon character with large round ears",
        "donald duck": "Disney cartoon character duck with blue sailor outfit",
        "cercei lannister": "character from Game of Thrones with blonde hair",
        "john pork": "cartoon pig character with a fedora hat",
        "ronald mcdonald": "McDonald's mascot clown with red and yellow outfit",
        "wendy": "Wendy's fast food mascot with red hair in pigtails",
        "eric cartman": "South Park cartoon character, 8-year-old boy with chubby face, brown hair, overweight body, wearing red coat, blue mittens, yellow-trimmed cyan hat with yellow pom-pom on top, brown pants, angry or smug expression, simplistic 2D flat cartoon style exactly like in South Park TV show"
    }
    
    name_lower = name.lower()
    for key in fictional_characters.keys():
        if key in name_lower or name_lower in key:
            return True
    
    return False

def get_character_description(name):
    """
    Get special description for known fictional characters.
    
    Args:
        name (str): Character name
        
    Returns:
        str: Character description for the prompt
    """
    fictional_characters = {
        "peter griffin": "animated character from Family Guy with round face, double chin, glasses, green pants, white shirt, cartoon style",
        "stewie griffin": "infant character from Family Guy with football-shaped head, red overalls, yellow shirt, disproportionately large head, small body, evil genius expression, brandishing ray gun, Family Guy animation style",
        "stewie": "infant character from Family Guy with football-shaped head, red overalls, yellow shirt, disproportionately large head, small body, evil genius expression, brandishing ray gun, Family Guy animation style",
        "homer simpson": "yellow cartoon character from The Simpsons with bald head, white shirt, blue pants",
        "bart simpson": "yellow cartoon character with spiky hair from The Simpsons, orange shirt, blue shorts",
        "mickey mouse": "Disney cartoon character with large round ears, red shorts with white buttons, yellow shoes",
        "donald duck": "Disney cartoon character duck with blue sailor outfit and hat, orange bill and feet",
        "cercei lannister": "character from Game of Thrones with long blonde hair, regal appearance, green eyes, elegant red and gold clothing, serious expression",
        "john pork": "friendly cartoon pig with a brown fedora hat, bow tie, cheerful expression, anthropomorphic pig character, clean cartoon style",
        "ronald mcdonald": "McDonald's mascot clown with bright red hair, yellow jumpsuit with red and white striped sleeves, red and white face paint, big red shoes, friendly and cheerful expression",
        "wendy": "Wendy's restaurant mascot with bright red hair in pigtails tied with blue ribbons, freckles, blue and white striped dress, friendly smile, cartoon style",
        "eric cartman": "South Park cartoon character, 8-year-old boy with chubby face, brown hair, overweight body, wearing red coat, blue mittens, yellow-trimmed cyan hat with yellow pom-pom on top, brown pants, angry or smug expression, simplistic 2D flat cartoon style exactly like in South Park TV show"
    }
    
    name_lower = name.lower()
    
    # Check for exact matches first
    for key, description in fictional_characters.items():
        if key == name_lower:
            return description
    
    # Check for partial matches if no exact match
    for key, description in fictional_characters.items():
        if key in name_lower or name_lower in key:
            return description
    
    return ""

def generate_teacher_image(teacher_name, output_dir="info_videos/assets/teachers", character_description=None):
    """
    Generates an image of a teacher with white background and removes the background.
    Now supports cartoon and fictional characters with better prompts.
    
    Args:
        teacher_name (str): Name of the teacher (e.g., "Professor Sarah Johnson")
        output_dir (str): Directory to save the images
        character_description (str, optional): Custom description for the character
        
    Returns:
        str: Path to the generated transparent PNG of the teacher
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if we have an existing image first (to avoid regenerating)
    transparent_path = os.path.join(output_dir, f"{teacher_name.replace(' ', '_')}_transparent.png")
    if os.path.exists(transparent_path):
        print(f"  Using existing image for {teacher_name}")
        return transparent_path
        
    # Generate prompt based on whether it's a fictional character
    if character_description:
        # Use the provided character description for custom fictional characters
        prompt = f"High-quality image of {teacher_name}, {character_description}, against a plain white background, full-body, centered, professional quality"
    elif is_fictional_character(teacher_name):
        character_desc = get_character_description(teacher_name)
        prompt = f"High-quality image of {teacher_name}, {character_desc}, against a plain white background, full-body, centered, professional quality"
    else:
        prompt = f"Professional headshot photograph of {teacher_name}, professor, teacher, mentor, on plain white background, high quality, detailed, realistic"
    
    try:
        # Generate image with white background
        img_streams = generate_images_with_imagen(prompt=prompt, aspect_ratio="1:1")
        original_image = Image.open(img_streams[0])
        
        # Save original image
        original_path = os.path.join(output_dir, f"{teacher_name.replace(' ', '_')}_original.png")
        original_image.save(original_path)
        
        # Remove background
        image_with_transparent_bg = remove(original_image)
        
        # Save image with transparent background
        image_with_transparent_bg.save(transparent_path, format="PNG")
        
        return transparent_path
    
    except Exception as e:
        print(f"❌ Failed to generate teacher image: {e}")
        return None

def generate_teachers_images(teacher1_name, teacher2_name, output_dir="info_videos/assets/teachers", teacher1_description=None, teacher2_description=None):
    """
    Generates images for two teachers with white backgrounds and removes the backgrounds.
    
    Args:
        teacher1_name (str): Name of the first teacher
        teacher2_name (str): Name of the second teacher
        output_dir (str): Directory to save the images
        teacher1_description (str, optional): Custom description for the first teacher
        teacher2_description (str, optional): Custom description for the second teacher
        
    Returns:
        tuple: Paths to the generated transparent PNGs of both teachers
    """
    print(f"Generating image for {teacher1_name}...")
    teacher1_image = generate_teacher_image(teacher1_name, output_dir, character_description=teacher1_description)
    
    print(f"Generating image for {teacher2_name}...")
    teacher2_image = generate_teacher_image(teacher2_name, output_dir, character_description=teacher2_description)
    
    return teacher1_image, teacher2_image

def generate_content_image(text_segment, output_dir="info_videos/assets/content_images"):
    """
    Generates an image related to the content of a text segment.
    
    Args:
        text_segment (str): Text segment to generate an image for
        output_dir (str): Directory to save the images
        
    Returns:
        str: Path to the generated image
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a descriptive prompt based on the text segment
    # Explicitly mention no text to ensure images don't have text overlays
    prompt = f"Educational illustration showing {text_segment}, clear, informative, detailed, professional style, no text, no captions, no labels"
    
    try:
        img_streams = generate_images_with_imagen(prompt=prompt)
        image = Image.open(img_streams[0])
        
        # Generate a unique filename based on the first few words of the text
        filename = "_".join(text_segment.split()[:5]).lower()
        filename = ''.join(c if c.isalnum() or c == '_' else '_' for c in filename)
        path = os.path.join(output_dir, f"{filename[:50]}.png")
        
        image.save(path)
        return path
    
    except Exception as e:
        print(f"❌ Failed to generate content image: {e}")
        return None

def generate_topic_images(topics, output_dir="info_videos/assets/content_images"):
    """
    Generates a set of high-quality images for specific topics.
    This approach creates better visuals than generating from script segments.
    
    Args:
        topics (list): List of specific topics to generate images for
        output_dir (str): Directory to save the images
        
    Returns:
        list: Paths to the generated images
    """
    os.makedirs(output_dir, exist_ok=True)
    
    image_paths = []
    for i, topic in enumerate(topics):
        print(f"  Generating image for topic: {topic} ({i+1}/{len(topics)})")
        
        # Create a more focused, high-quality prompt for educational imagery
        prompt = f"Professional educational illustration of {topic}, high-quality visualization, clear detailed diagram, informative, textbook style, clean background, no text or labels, suitable for an educational presentation"
        
        try:
            img_streams = generate_images_with_imagen(prompt=prompt)
            if not img_streams or len(img_streams) == 0:
                print(f"❌ No image generated for topic '{topic}'")
                continue
                
            image = Image.open(img_streams[0])
            
            # Generate a unique filename based on the topic and index
            # Using the index ensures we don't overwrite previous images even with similar topics
            filename = f"topic_{i+1}_" + "_".join(topic.split()[:5]).lower()
            filename = ''.join(c if c.isalnum() or c == '_' else '_' for c in filename)
            path = os.path.join(output_dir, f"{filename[:50]}.png")
            
            print(f"  Saving image to: {path}")
            image.save(path)
            image_paths.append(path)
            
        except Exception as e:
            print(f"❌ Failed to generate image for topic '{topic}': {e}")
    
    if not image_paths:
        print("⚠️ No images were successfully generated. Creating a default image.")
        try:
            # Create a default image as fallback
            prompt = "Generic educational diagram with abstract concept visualization"
            img_streams = generate_images_with_imagen(prompt=prompt)
            if img_streams and len(img_streams) > 0:
                image = Image.open(img_streams[0])
                path = os.path.join(output_dir, "default_topic_image.png")
                image.save(path)
                image_paths.append(path)
        except Exception as e:
            print(f"❌ Failed to create even a default image: {e}")
    
    return image_paths

def generate_wine_comparison_images(output_dir="info_videos/assets/content_images"):
    """
    Generates a predefined set of high-quality images for wine comparison presentations.
    
    Args:
        output_dir (str): Directory to save the images
        
    Returns:
        list: Paths to the generated images
    """
    wine_topics = [
        "French wine map showing Burgundy and Bordeaux regions",
        "Pinot Noir grapes in Burgundy vineyards",
        "Cabernet Sauvignon and Merlot blend grapes in Bordeaux",
        "Burgundy wine bottles and glasses with light-bodied red wine",
        "Bordeaux wine bottles and glasses with full-bodied red wine",
        "Wine cellar with French wine barrels",
        "Château in Bordeaux wine region"
    ]
    
    return generate_topic_images(wine_topics, output_dir)

# Predefined topic collections for common educational subjects
TOPIC_COLLECTIONS = {
    "wine_comparison": [
        "French wine map showing Burgundy and Bordeaux regions",
        "Pinot Noir grapes in Burgundy vineyards",
        "Cabernet Sauvignon and Merlot blend grapes in Bordeaux",
        "Burgundy wine bottles and glasses with light-bodied red wine",
        "Bordeaux wine bottles and glasses with full-bodied red wine"
    ],
    "nutrition": [
        "Balanced nutrition plate with various food groups",
        "Essential micronutrients and vitamins diagram",
        "Colorful phytochemical-rich fruits and vegetables",
        "Dietary fiber and digestive health illustration",
        "Hydration and water balance in human body",
        "Nutrient timing and absorption diagram",
        "Gut microbiome and its role in health"
    ],
    "climate_change": [
        "Global temperature increase graph",
        "Melting ice caps and glaciers",
        "Extreme weather events like hurricanes and floods",
        "Greenhouse gas emissions from factories and vehicles",
        "Renewable energy solutions like solar and wind farms"
    ],
    "solar_system": [
        "The Sun and all planets to scale",
        "Earth and Moon system",
        "Jupiter and its moons",
        "Saturn with its distinctive rings",
        "Asteroid belt between Mars and Jupiter"
    ]
}

def get_topic_collection(collection_name):
    """
    Returns a predefined collection of topics for generating images.
    
    Args:
        collection_name (str): Name of the topic collection
        
    Returns:
        list: List of topics in the collection
    """
    return TOPIC_COLLECTIONS.get(collection_name, []) 