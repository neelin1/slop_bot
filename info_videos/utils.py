import os
import PyPDF2

def extract_text_from_pdf(pdf_path):
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text content
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        text_content = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract text from each page
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_content += page.extract_text() + "\n\n"
        
        return text_content.strip()
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def verify_image_files(image_paths):
    """
    Verify that all provided image paths exist and are valid image files.
    
    Args:
        image_paths (list): List of image file paths
        
    Returns:
        list: List of valid image file paths
    """
    valid_image_paths = []
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    
    for path in image_paths:
        if os.path.exists(path):
            # Check if it's an image file
            ext = os.path.splitext(path)[1].lower()
            if ext in valid_extensions:
                valid_image_paths.append(path)
            else:
                print(f"Warning: File is not an image format: {path}")
        else:
            print(f"Warning: Image file not found: {path}")
    
    return valid_image_paths 