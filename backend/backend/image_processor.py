import pytesseract
from PIL import Image
import cv2
import numpy as np

def extract_text_from_screenshot(image_path):
    """
    Extract text from iPhone screenshots with preprocessing for better accuracy.
    
    Args:
        image_path (str): Path to the screenshot image
        
    Returns:
        str: Extracted text
    """
    # Read image
    image = cv2.imread(image_path)
    
    # Convert to RGB (OpenCV uses BGR)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Preprocessing
    # Resize if image is too large (maintain aspect ratio)
    max_dimension = 1800
    height, width = image.shape[:2]
    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)
        image = cv2.resize(image, None, fx=scale, fy=scale)
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # Apply thresholding to preprocess the image
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # Apply dilation to connect text components
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    gray = cv2.dilate(gray, kernel, iterations=1)
    
    # OCR Configuration
    custom_config = r'--oem 3 --psm 6'
    
    try:
        # Perform OCR
        text = pytesseract.image_to_string(gray, config=custom_config)
        return text.strip()
    except Exception as e:
        raise Exception(f"Error during OCR: {str(e)}")

# Usage example
if __name__ == "__main__":
    try:
        text = extract_text_from_screenshot("screenshot.png")
        print("Extracted text:")
        print(text)
    except Exception as e:
        print(f"Error: {str(e)}")
