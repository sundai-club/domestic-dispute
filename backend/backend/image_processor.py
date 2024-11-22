import pytesseract
from PIL import Image
import cv2
import numpy as np
from PIL.ExifTags import TAGS
import os
from datetime import datetime
from ai import extract_text
    
def get_image_creation_time(image_path):

    try:
        image = Image.open(image_path)
        exif = image.getexif()
        
        if exif:
            print(exif)
            for tag_id in exif:
                tag = TAGS.get(tag_id, tag_id)
                data = exif.get(tag_id)
                if tag == 'DateTime':
                    return data
        return datetime.fromtimestamp(os.path.getctime(image_path))
    except Exception as e:
        print(f"Error reading image metadata: {e}")
        return None
def extract_text_from_multiple(image_paths):
    # Sort images by creation time
    sorted_paths = sorted(
        image_paths,
        key=lambda x: get_image_creation_time(x) or datetime.now()
    )
    
    # Process images in order
    all_texts = []
    for path in sorted_paths:
        text = extract_text(path)
        all_texts.append(text)
    
    return "\n".join(all_texts)

def sort_images_chronologically(image_paths):
    """
    Args:
        image_paths (list): List of paths to images
        
    Returns:
        list: Sorted list of image paths from oldest to newest
    """
    # Create a list of tuples (path, timestamp)
    dated_paths = []
    for path in image_paths:
        timestamp = get_image_creation_time(path)
        if timestamp:
            # Convert string datetime to datetime object if needed
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.strptime(timestamp, '%Y:%m:%d %H:%M:%S')
                except ValueError:
                    timestamp = datetime.fromtimestamp(os.path.getctime(path))
            dated_paths.append((path, timestamp))
        else:
            # Fallback to file creation time
            creation_time = datetime.fromtimestamp(os.path.getctime(path))
            dated_paths.append((path, creation_time))
    
    sorted_paths = sorted(dated_paths, key=lambda x: x[1])
    return [path for path, _ in sorted_paths]

#print(sort_images_chronologically(["/Users/seanklein/Projects/Github/homewrecker_ai/backend/backend/images/IMG_0145.PNG", "/Users/seanklein/Projects/Github/homewrecker_ai/backend/backend/images/IMG_0144.PNG"]))