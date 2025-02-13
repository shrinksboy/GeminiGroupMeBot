#Jonah Casimir GroupMe Gemini Chatbot
################################################################################################################################

from google import genai
from google.cloud import datastore
import http
from flask import Flask, request, jsonify # type: ignore
import logging
import os
import requests
from PIL import Image
from io import BytesIO

app = Flask(__name__)

# Load environment variables
BOT_ID = os.environ.get("BOT_ID")  # Get Groupme bot ID from the environment
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")  # Get google api key from the environment
GROUPME_API_URL = "https://api.groupme.com/v3/bots/post"  # GroupMe API endpoint
GROUP_ADMIN_ID = os.environ.get("GROUP_ADMIN_ID") # Groupme sender_id that has admin rights

client = genai.Client(api_key=GOOGLE_API_KEY)
chatgroup_id = 96641973

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Initialize logging for (develop branch)")

# Initialize Cloud Datastore client
datastore_client = datastore.Client()
logger.info("Initialize datastore for (develop branch)")

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
        sender_name = v3_message.get("name", "Unknown Sender")  # Get sender name, default to "Unknown Sender"
        message_text = v3_message.get("text", "")  # Get message text, default to empty string
        group_id = v3_message.get("group_id", "Unknown Group")
        sender_id = v3_message.get("sender_id", "Unknown Sender ID")
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
            send_response(response_text="Test Successful - (Development Branch)")

        #Admin Tests ######
        if sender_id is GROUP_ADMIN_ID:
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
                 

        # Check if chatbot response needs to be sent back
        if message_text.lower().startswith("@chatius"):
             
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
     client = genai.Client(api_key=GOOGLE_API_KEY)
     if image is None:
        response = client.models.generate_content(
        model="gemini-2.0-flash", contents=input_text
        )
     else:
         response = client.models.generate_content(
        model="gemini-2.0-flash", contents=[input_text, image]
        )
     
     return response.text

def get_chat_session(chat_id):
    """Retrieves chat session from Cloud Datastore."""
    key = datastore_client.key("ChatSession", chat_id)
    entity = datastore_client.get(key)
    if entity is None:
        # Create a new chat session if it doesn't exist
        model = genai.GenerativeModel('gemini-pro')
        chat = model.start_chat()
        entity = datastore.Entity(key=key)
        entity["session"] = chat.get_history()  # Store initial chat history
        datastore_client.put(entity)
        return chat
    else:
        model = genai.GenerativeModel('gemini-pro')
        chat = model.start_chat(history = entity["session"])
        # Load History

        return chat
    
def save_chat_session(chat_id, chat):
    """Saves the chat history to Cloud Datastore."""
    key = datastore_client.key("ChatSession", chat_id)
    entity = datastore.Entity(key=key)
    entity["session"] = chat.get_history()
    datastore_client.put(entity)


@app.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint for Google Cloud
    """
    return "OK", 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))