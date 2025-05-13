import os
import PyPDF2
import io
from PIL import Image

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def convert_webp_to_png(webp_path):
    """
    Convert a .webp image to .png format.
    
    Args:
        webp_path (str): Path to the .webp file
        
    Returns:
        str: Path to the converted .png file, or None if conversion failed
    """
    try:
        # Create output path by changing extension
        png_path = os.path.splitext(webp_path)[0] + '.png'
        
        # Open and convert the image
        with Image.open(webp_path) as img:
            # If image has transparency (RGBA), preserve it
            if img.mode == 'RGBA':
                img.save(png_path, 'PNG')
            else:
                # Convert to RGB if not already
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(png_path, 'PNG')
        
        print(f"Converted {webp_path} to {png_path}")
        return png_path
    except Exception as e:
        print(f"Error converting webp to png: {e}")
        return None

def verify_image_files(image_paths):
    """
    Verify that provided file paths are valid image files.
    Automatically converts .webp files to .png format.
    
    Args:
        image_paths (list): List of image file paths
        
    Returns:
        list: List of valid image file paths (may include converted .png files)
    """
    valid_images = []
    
    for path in image_paths:
        try:
            # Check if file exists
            if not os.path.exists(path):
                print(f"Warning: File does not exist: {path}")
                continue
                
            # For .webp files, convert to PNG
            if path.lower().endswith('.webp'):
                print(f"Converting .webp file to PNG: {path}")
                png_path = convert_webp_to_png(path)
                if png_path and os.path.exists(png_path):
                    valid_images.append(png_path)
                    continue
                else:
                    print(f"Warning: Failed to convert .webp file: {path}")
            
            # For other formats, validate by trying to open with PIL
            try:
                with Image.open(path) as img:
                    # If we can open it, it's a valid image
                    valid_images.append(path)
            except Exception as e:
                print(f"Warning: File is not an image format: {path}")
        except Exception as e:
            print(f"Error validating image file {path}: {e}")
    
    return valid_images 