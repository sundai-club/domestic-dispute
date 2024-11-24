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
from typing import List

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
    # This function can be removed as we're not using file paths anymore
    pass

def extract_text(path):
    image_path = Path(__file__).parent / path
    base64_image = encode_image(image_path)
    llm = ChatOpenAI(
        model="gpt-4o-2024-11-20",
        max_tokens=1024,
    )
    
    message = HumanMessage(
        content=[
            {"type": "text", "text": "Transribe these iphone screenshots. They are provided in either chronological or reverse chronological order. Based on the messages determine which order they are in. Make sure the output is in the format of a conversation between two people. with each message on a new line and beginnign with the name. Include emojis.The name of party 2 is at the top of the text. The name of party 1 is unknown and you should just put in a placeholder of 'sender'."},
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


def extract_multiple_text(base64_images: List[str]) -> str:
    """
    Process multiple base64-encoded images and combine their text
    Args:
        base64_images: List of base64-encoded image strings
    Returns:
        Combined conversation text
    """
    messages_content = []
    messages_content.append({
        "type": "text",
        "text": """Transcribe these iPhone screenshots. Include emojis. The name of party 2 is at the top of the text. 
        The name of party 1 is unknown and you should just put in a placeholder of 'sender'.
        Your output should be in the following format:
        sender: message
        sender: message
        If one party sends multiple messages, you should rewrite their name each on each line.
        Senders name should be in all caps and not have any additional formatting."""
    })

    for base64_img in base64_images:
        messages_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_img}"
            }
        })

    llm = ChatOpenAI(
        model="gpt-4o-2024-11-20",
        max_tokens=1024,
    )
    
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": "Here are multiple iPhone screenshots of a conversation. Process them and combine them into a single chronological conversation."
            },
            *messages_content
        ]
    )
    
    response = llm.invoke([message])
    return response.content

def sort_images_chronologically(image_paths):
    # This function can be removed as sorting is now done in the upload endpoint
    pass

def extract_text_with_metadata(paths):
    # This function can be removed as we're using the new extract_multiple_text
    pass



#print(extract_text_with_metadata(["IMG_0145.PNG", "IMG_0144.PNG"]))

