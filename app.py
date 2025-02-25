#Jonah Casimir GroupMe Gemini Chatbot
################################################################################################################################

import datetime
from google.genai.types import GenerateContentConfig, HttpOptions
from google import genai
from google.cloud import datastore
import http
from flask import Flask, request, jsonify # type: ignore
import logging
import os
import requests
from PIL import Image # type: ignore
from io import BytesIO
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

app = Flask(__name__)

# Load environment variables
BOT_ID = os.environ.get("BOT_ID")  # Get Groupme bot ID from the environment
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")  # Get google api key from the environment
GROUPME_API_URL = "https://api.groupme.com/v3/bots/post"  # GroupMe API endpoint
IMAGE_SERVICE_URL = "https://image.groupme.com"
GROUP_ADMIN_ID = os.environ.get("GROUP_ADMIN_ID") # Groupme sender_id that has admin rights

client = genai.Client(api_key=GOOGLE_API_KEY)
chatgroup_id = 96641973

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Initialize logging for (develop branch)")

# Initialize Cloud Firestore client
logger.info("Initialize datastore for (develop branch)")
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
    'projectId': "stunning-symbol-450620-m7",
})

db = firestore.client()

# Create data
doc_ref = db.collection("logs").document("test")
doc_ref.set({
    "timestamp": "NOW()",
    "message": "Testing testing"
})


@app.route('/', methods=['POST'])
def webhook_handler():
    """
    Handles incoming POST requests from the V3 message provider (GroupMe).
    """
    logger.info("Received request from webhook.")

    try:
        # Extract data from the request
        data = request.get_json()

        # Process the V3 message (Implement your logic here)
        if data:
            logger.info(f"Received V3 message: {data}")
            response_message = process_message(data)  # Call function to handle the processing
        else:
            logger.warning("No data received in the request.")
            return jsonify({"status": "error", "message": "No data received"}), 400  # Bad Request

        # Create a response
        response_data = {
            "status": "success",
            "response": "Message processed" #success message
        }
        logger.info(f"Sending response: {response_data}")
        return jsonify(response_data), 200  # OK

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500  # Internal Server Error


def process_message(v3_message):
    """
    Process the V3 message (GroupMe message) and generate a response.
    """

    try:
        # Extract relevant information from the message
        message_id = v3_message.get("id") # get id of v3 message
        sender_name = v3_message.get("name", "Unknown Sender")  # Get sender name, default to "Unknown Sender"
        message_text = v3_message.get("text", "")  # Get message text, default to empty string
        group_id = v3_message.get("group_id", "Unknown Group")
        sender_id = v3_message.get("sender_id", "Unknown Sender ID")
        sender_type = v3_message.get("sender_type")
        message_timestamp = convert_timestamp(v3_message.get("created_at")) # get timestamp and convert from epoch time
        attachments = v3_message.get("attachments", [])

        # Grab image url if there is one
        image_url = None
        if attachments:
            for attachment in attachments:
                if attachment.get("type") == "image":
                    image_url = attachment.get("url")
                    logger.info("Got image URL")
                    break # break so other attachments are ignored

        # Status test
        if "bot-status-test" in message_text.lower():
            logger.info("BOT STATUS: GOOD")
            logger.info("sender_id " + sender_id)
            send_response(response_text="Test Successful - (Development Branch) - v2.5")
            
        #Admin Tests ######
        if sender_id == GROUP_ADMIN_ID:
            logger.info("Message from ADMIN")

            # Image test
        if "bot-image-test" in message_text.lower():
            logger.info("Image Sending Test")
            send_response(response_text="Image Test", image_url="https://i.groupme.com/630x630.jpeg.6772b62a25f94ac09169928658de6612")

            # Image upload
        if "bot-image-analyze-test" in message_text.lower():
            logger.info("Image analyzer test")
            attachment_image = load_image("https://i.groupme.com/630x630.jpeg.6772b62a25f94ac09169928658de6612")
            response_text = gemini_request("analyze this image", attachment_image)
            send_response(response_text)


        # Add message to database
        doc_ref = db.collection("dev-logs").document(message_id)
        doc_ref.set({
            "timestamp": message_timestamp,
            "sender ID": sender_id,
            "sender name": sender_name,
            "sender type": sender_type,
            "message": message_text
        })
                 

        # Check if chatbot response needs to be sent back
        if message_text.lower().startswith("@chatius-art"):
            message_text = message_text[len("@chatius-art"):].strip() # Remove "@chatius-art" from the beginning of the message

            generated_image_url = imagen_request(message_text)
            response_text = "Here's your image, human"

            send_response(response_text, generated_image_url)

        elif message_text.lower().startswith("@chatius"):
             
             message_text = message_text[len("@chatius"):].strip() # Remove "@chatius" from the beginning of the message

             image = load_image(image_url) if image_url else None

             response_text = gemini_request(message_text, image)
             send_response(response_text)

        

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return f"Error processing message: {e}"  # Return an error message to the webhook caller
    

# Load image from URL to attach to message
def load_image(image_url):
     try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        image = Image.open(BytesIO(response.content))
        return image
     except requests.exceptions.RequestException as e:
        logger.error(f"Error loading image from URL: {e}")
        return None
     
    
def send_response(response_text, image_url=None):
    """
    Send POST response to groupme
    """

    if image_url is None: # Add Image to payload if one exists
         response_payload = {
                  "bot_id": BOT_ID,
                "text": response_text
             }
    else:
         response_payload = {
                  "bot_id": BOT_ID,
                "text": response_text,
                "attachments": [
                     {
                          "type" : "image",
                          "url" : image_url
                     }
                ]
             }

    try:
            response = requests.post(GROUPME_API_URL, json=response_payload)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            logger.info(f"Successfully sent message to GroupMe. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
            logger.error(f"Error sending message to GroupMe: {e}")
            return f"Error sending message to GroupMe: {e}"

    return "Message sent to GroupMe."  # success message

##########################################

def gemini_request(input_text, image=None):
     """
     Sends text and possible attached image to gemini api and returns text response
     """
     client = genai.Client(api_key=GOOGLE_API_KEY)
     # System Instructions for gemini
     sys_instruct = "You are a chatbot in a GroupMe group chat. Your name is Chatius."

     if image is None:
         chat = client.chats.create(model="gemini-2.0-flash",
                                    # config=GenerateContentConfig(system_instruction=sys_instruct),
                                    history=get_chat_history_from_firestore)
         response = chat.send_message(input_text)

        # response = client.models.generate_content(
        # model="gemini-2.0-flash", contents=input_text
        # )
     else:
        response = client.models.generate_content(
        model="gemini-2.0-flash", contents=[input_text, image]
        )
     
     return response.text

def imagen_request(input_text):
    """
     Sends text to imagen api and returns image url response
    """
    response = client.models.generate_images(
        model='imagen-3.0-generate-002',
        prompt= input_text 
    )
    for generated_image in response.generated_images:
        image = Image.open(BytesIO(generated_image.image.image_bytes))
        
    gen_image_url = upload_image_to_groupme(image_to_bytes(image))
    return gen_image_url

    
##########################################

def convert_timestamp(timestamp):
    """Converts a Unix timestamp to a datetime object."""
    try:
        # Convert the timestamp to a datetime object (in UTC)
        datetime_object = datetime.datetime.utcfromtimestamp(timestamp)
        # Format the datetime object as a string
        formatted_datetime = datetime_object.strftime("%Y-%m-%d %H:%M:%S UTC")
        return formatted_datetime
    except Exception as e:
        print(f"Error converting timestamp: {e}")
        return None

def image_to_bytes(image):
    """Converts a PIL Image object to bytes."""
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='JPEG')  # You can change the format here (e.g., PNG)
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr

def upload_image_to_groupme(image_bytes):
    """Uploads image bytes to the GroupMe Image Service and returns the URL."""
    try:
        files = {'file': image_bytes}  # The key "file" is required by the GroupMe API
        response = requests.post(IMAGE_SERVICE_URL, files=files)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        return data.get("payload")  # The image URL is in the "payload" field
    except requests.exceptions.RequestException as e:
        print(f"Error uploading image to GroupMe: {e}")
        return None
    

def get_chat_history_from_firestore(group_id):
    """Retrieves the entire chat history from Firestore for a given group and formats it for Gemini."""
    chat_history = []
    try:
        # Reference to the "dev-logs" collection
        messages_ref = db.collection("dev-logs")

        # Retrieve all documents in the "dev-logs" collection, ordered by timestamp
        docs = messages_ref.order_by("timestamp").get()

        # Iterate over the documents and append them to the history list
        for doc in docs:
            message_data = doc.to_dict()
            message = message_data.get("message", "")
            sender_type = message_data.get("sender type", "")
            sender_name = message_data.get("sender name", "Unknown")

            # Determine the role based on sender type
            if sender_type == "user":
                role = "user"
            elif sender_type == "bot":
                role = "model" # Use model role for bot responses. In this case, what does the bot do?
            else:
                role = "user"  # or you can skip this document

            # Format each entry to contain name, message, and whether the sender is a bot
            formatted_data = {
            f"The sender name is {sender_name} and the message is {message}",
            role,
            }

            chat_history.append(formatted_data)

    except Exception as e:
        print(f"Error retrieving chat history from Firestore: {e}")
    return chat_history


@app.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint for Google Cloud
    """
    return "OK", 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))