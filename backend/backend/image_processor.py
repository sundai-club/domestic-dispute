import pytesseract
from PIL import Image
import cv2
import numpy as np
from PIL.ExifTags import TAGS
import os
from datetime import datetime
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import base64
from dotenv import load_dotenv
from pathlib import Path
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_community.document_loaders.image import UnstructuredImageLoader
import getpass

load_dotenv()

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")
_set_env("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "langchain-academy"
def get_image_creation_time(image_path):

    try:
        image = Image.open(image_path)
        exif = image.getexif()
        
        if exif:
            for tag_id in exif:
                tag = TAGS.get(tag_id, tag_id)
                data = exif.get(tag_id)
                if tag == 'DateTime':
                    return data
        return datetime.fromtimestamp(os.path.getctime(image_path))
    except Exception as e:
        print(f"Error reading image metadata: {e}")
        return None
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_text(path):
    image_path = Path(__file__).parent / path
    base64_image = encode_image(image_path)
    llm = ChatOpenAI(
        model="gpt-4o-2024-11-20",
        max_tokens=1024,
    )
    
    message = HumanMessage(
        content=[
            {"type": "text", "text": "Transribe these iphone screenshots. They are provided in either or reverse chronological order. Based on the messages determine which order they are in. Make sure the output is in the format of a conversation between two people. with each message on a new line and beginnign with the name. Include emojis.The name of party 2 is at the top of the text. The name of party 1 is unknown and you should just put in a placeholder of 'sender'."},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }
            }
        ]
    )
    response = llm.invoke([message])
    #print(response.content)
    return response.content


def extract_multiple_text(paths):
    """
    Process multiple images and combine their text in chronological order
    Args:
        paths: List of image paths
    Returns:
        Combined conversation text
    """
    messages_content = []
    
    for path in paths:
        #image_path = Path(__file__).parent / path
        image_path = path
        base64_image = encode_image(image_path)
        
        messages_content.append({
            "type": "text", 
            #"text": "Transcribe this iPhone screenshot. Include emojis. The name of party 2 is at the top of the text. The name of party 1 is unknown and you should just put in a placeholder of 'sender'."
            "text": f"""Transcribe this iPhone screenshot. Include emojis. The name of party 2 is at the top of the text. The name of party 1 is unknown and you should just put in a placeholder of 'sender'.
            Your output should be in the following format:
            sender: message
            sender: message
            If one party sends multiple messages, you should rewrite their name each on each line.
            Senders name should be in all caps and not have any additional formatting.
            """
        })
        messages_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}"
            }
        })

    llm = ChatOpenAI(
        model="gpt-4o-2024-11-20",
        max_tokens=1024,
    )
    
    message = HumanMessage(
        content=[
            {"type": "text", 
             "text": "Here are multiple iPhone screenshots of a conversation. They are presented in timestamp order. This does not guaruntee that they were taken in ascending or descending order, but should serve as a guide.Process them and combine them into a single chronological conversation. Make sure the output is in the format of a conversation between two people, with each message on a new line and beginning with the name.The name of party 2 is at the top of the text. The name of party 1 is unknown and you should just put in a placeholder of 'sender'."},
            *messages_content
        ]
    )
    
    response = llm.invoke([message])
    return response.content

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

def extract_text_with_metadata(paths):
    """
    Extract text from images, combine with metadata, and stitch together chronologically
    Args:
        paths: List of image paths (now relative to backend/images)
    Returns:
        Stitched conversation text
    """
    # Convert relative paths to absolute paths
    base_path = Path(__file__).parent / "images"
    absolute_paths = [str(base_path / Path(path)) for path in paths]
    
    # Verify all files exist
    for path in absolute_paths:
        if not Path(path).exists():
            raise FileNotFoundError(f"Image file not found: {path}")
    
    # First pass: Extract text and metadata from each image
    image_data = []
    for path in absolute_paths:
        creation_time = get_image_creation_time(path)
        base64_image = encode_image(path)
        
        # Get initial text extraction
        llm = ChatOpenAI(model="gpt-4o-2024-11-20", max_tokens=1024)
        message = HumanMessage(
            content=[
                {"type": "text", "text": "Transcribe this iPhone screenshot. Include emojis and timestamps if visible."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                }
            ]
        )
        text_content = llm.invoke([message]).content
        
        image_data.append({
            "timestamp": creation_time,
            "text": text_content
        })
    
    # Sort by timestamp
    image_data.sort(key=lambda x: x["timestamp"])
    
    # Second pass: Stitch together with context
    context_message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": f"""Here are multiple transcribed iPhone screenshots with their timestamps. 
                Combine them into a single coherent conversation. Ensure it's chronologically correct. The timestamps are the order the screenshots were taken, and may not represent the true order. Use this as a guide. Ensure all texts from each message is included in your final output.
                Do not repeat content in the case of overlapping messages, but use the overlap as a guide to determine the correct order.

                Timestamps and content:
                {'\n'.join([f'[{data["timestamp"]}]:\n{data["text"]}' for data in image_data])}
                
                Please format the output as a conversation between two people, with each message on 
                a new line starting with the sender's name. Use 'sender' for party 1 and extract 
                party 2's name from the messages."""
            }
        ]
    )
    
    llm = ChatOpenAI(model="gpt-4o-2024-11-20", max_tokens=1024)
    final_response = llm.invoke([context_message])
    return final_response.content

print(extract_text_with_metadata(["IMG_0145.PNG", "IMG_0144.PNG"]))
