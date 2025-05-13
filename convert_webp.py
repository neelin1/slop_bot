from PIL import Image
import os

def convert_webp_to_png(input_path, output_path=None):
    """
    Convert a WEBP image to PNG format.
    
    Args:
        input_path (str): Path to the input WEBP file
        output_path (str, optional): Path to save the output PNG file
                                    If not provided, replaces .webp with .png
    
    Returns:
        str: Path to the converted PNG file
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        return None
    
    if output_path is None:
        # Replace .webp extension with .png
        output_path = os.path.splitext(input_path)[0] + ".png"
    
    try:
        # Open the WEBP image
        img = Image.open(input_path)
        
        # Save as PNG
        img.save(output_path, "PNG")
        
        print(f"Successfully converted {input_path} to {output_path}")
        return output_path
    except Exception as e:
        print(f"Error converting image: {str(e)}")
        return None

if __name__ == "__main__":
    # Convert the quantum computing image
    convert_webp_to_png("sample_images/Quantum-Computing-Explained.webp") 