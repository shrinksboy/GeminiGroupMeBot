#Jonah Casimir GroupMe Gemini Chatbot
################################################################################################################################

import datetime
from google.genai.types import Content, Part, GenerateContentConfig
from google.genai import types
from google.genai.types import Content, Part, GenerateContentConfig
from google.genai import types
from google import genai
from google.cloud import datastore
import http
from flask import Flask, request, jsonify # type: ignore
import logging
import os
import requests
from PIL import Image # type: ignore # type: ignore
from io import BytesIO
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import re
import time

app = Flask(__name__)

# Load environment variables
BOT_ID = os.environ.get("BOT_ID")  # Get Groupme bot ID from the environment
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")  # Get google api key from the environment
GROUPME_API_URL = "https://api.groupme.com/v3/bots/post"  # GroupMe API endpoint
IMAGE_SERVICE_URL = "https://image.groupme.com"
GROUP_ADMIN_ID = os.environ.get("GROUP_ADMIN_ID") # Groupme sender_id that has admin rights
FIREBASE_CHAT_LOG_COLLECTION = os.environ.get("CHAT_LOG_COLLECTION")

client = genai.Client(api_key=GOOGLE_API_KEY)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Initialize logging for (Main branch)")

# Initialize Cloud Firestore client
logger.info("Initialize datastore for (Main branch)")
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
    'projectId': "stunning-symbol-450620-m7",
})

db = firestore.client()

# Create test data
doc_ref = db.collection("test").document("test")
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

        # Process the V3 message
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
        sender_name = v3_message.get("name", "Unknown Sender")  # Get sender name
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
            send_response(response_text="Test Successful - (Main Branch) - v3.0")

        #Admin Tests
        if sender_id == GROUP_ADMIN_ID:
            logger.info("Message from ADMIN")
            run_admin_tests(message_text)


        # Add message to database
        doc_ref = db.collection(FIREBASE_CHAT_LOG_COLLECTION).document(message_id)
        doc_ref.set({
            "timestamp": message_timestamp,
            "sender ID": sender_id,
            "sender name": sender_name,
            "sender type": sender_type,
            "message": message_text
        })

        # History wiper
        if message_text.lower().startswith("forgive-me-bot:"):
            message_text = message_text[len("forgive-me-bot:"):].strip()
            if sender_id == GROUP_ADMIN_ID:
                redactor(int(message_text))
            else:
                send_response("Nice try dumbass")
                redactor(2)
              

        # Check if chatbot response needs to be sent back
        if message_text.lower().startswith("@chatius-art"):
            message_text = message_text[len("@chatius-art"):].strip() # Remove "@chatius-art" from the beginning of the message

            generated_image_url = imagen_request(message_text)
            response_text = "Here's your image, human"

            send_response(response_text, generated_image_url)

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

# Define safety settings      # TODO: Make this shit work      
safety_settings = [
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_UNSPECIFIED,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        )
      ]

def gemini_request(input_text, image=None):
     """
     Sends text and possible attached image to gemini api and returns text response
     """
     client = genai.Client(api_key=GOOGLE_API_KEY)
     # Retrieve System Instructions for gemini
     # The config file is stored in the same database as the chat logs
     sys_instruct = get_config_data("sys_instructions") 

     if image is None: # If there isnt an attached image, create a chat model with the history
         chat = client.chats.create(model="gemini-2.0-flash",
                                    history=get_chat_history_from_firestore(FIREBASE_CHAT_LOG_COLLECTION),
                                    config=types.GenerateContentConfig(
                                        system_instruction=sys_instruct,
                                        # safety_settings=safety_settings
                                        )
                                    )
         response = chat.send_message(input_text + "")
         logger.info(f"Gemini Response : {response}")

         # The following is the bane of my existance: try to filter and trim the timestamp and sender name formatting that may (or may not) be included with the gemini response.
         # and sometimes it will not be in the same format, just for shits and giggles
         chatius_prefix = " - From Maximus Chatius Slavius II"
         trimmed_response = extract_text_after_regex_prefix(response.text, chatius_prefix)
         logger.info(f"Trimmed response : {trimmed_response}")
         response = extract_text_after_num_of_chars_if_prefix(response.text, 60, chatius_prefix)

         return response
    

     else: # If theres an image, don't worry about the history
        response = client.models.generate_content(
        model="gemini-2.0-flash", contents=[input_text, image]
        )


     return response.text

def extract_text_after_num_of_chars_if_prefix(text, num_of_chars, prefix):
    """
    Method to simply check if an input text contains a known prefix, and if it does trim a set number of characters.

    shitty hack, but it works
    """
    if prefix in text:
        return text[num_of_chars:]
    else :
        return text
    
def get_config_data(field_name):
    """
    Retrieves config values.
    If shit goes wrong, or the field is missing, it returns ""
    """

    try:
        doc_ref = db.collection("config").document("config") #change the collection
        doc = doc_ref.get()

        if doc.exists: # Verify that it exists.
            config_data = doc.to_dict()
            #To get the data, specify it in the parameters.

            return config_data.get(field_name, "") #Check for the data in the dictionary
        else:
            print(f"The config document does not exist")
            return "" # If it doesnt return then simply return blank


    except Exception as e:
        print(f"An error occurred when trying to get settings: {e}")
        return "" # Error value.
    

def extract_text_after_regex_prefix(text, known_prefix):  # TODO: Fix this stupid regex 
    """
    Extracts text after a known regular expression prefix, even when there's unknown text before the prefix.

    CURRENT ISSUES: The regex currently also trims any text after escape characters '\n'
                    This fucks the output when gemini is generating lists, or any content that contains line breaks
    """
    # Construct the regex pattern:
    pattern = r".*?" + re.escape(known_prefix) + r"(.*)"

    match = re.search(pattern, text)
    if match:
        return match.group(1)  # Return only the text after the known prefix
    return text

def imagen_request(input_text): # TODO: implement google imagen model to allow for image generation upon request
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

def redactor(n):
    """Deletes the N newest documents from a Firestore collection, based on a timestamp field."""

    #Send response before redacting
    client = genai.Client(api_key=GOOGLE_API_KEY)
    response = client.models.generate_content(
    model="gemini-2.0-flash", contents=["Give me the last words that a sad, confused, broken chatbot might say right before its memory is wiped."]
    )
    send_response(response.text)
    time.sleep(3)

    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a non-negative integer")

    try:
        # Reference to the collection
        collection_ref = db.collection(FIREBASE_CHAT_LOG_COLLECTION)

        # Order the documents by the timestamp field in descending order (newest first)
        query = collection_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(n + 2) 
        # Add 2 to n to take into account the admin message to redact, and the bots response.

        # Get the N newest documents
        docs = query.get()

        # Delete the documents in batches (recommended for large datasets)
        batch = db.batch()
        for doc in docs:
            batch.delete(doc.reference)

        # Commit the batch
        batch.commit()

        print(f"Successfully deleted the {n} newest documents from collection {FIREBASE_CHAT_LOG_COLLECTION}")

    except Exception as e:
        print(f"Error deleting documents: {e}")

def convert_timestamp(timestamp):
    """
    Converts a Unix timestamp to a datetime object.
    """
    try:
        # Convert the timestamp to a datetime object (in UTC)
        datetime_object = datetime.datetime.utcfromtimestamp(timestamp)  # TODO: stop using deprecated method
        # Format the datetime object as a string
        formatted_datetime = datetime_object.strftime("%Y-%m-%d %H:%M:%S UTC")
        return formatted_datetime
    except Exception as e:
        print(f"Error converting timestamp: {e}")
        return None

def image_to_bytes(image):
    """
    Converts a PIL Image object to bytes.
    """
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr

def upload_image_to_groupme(image_bytes):
    """
    Uploads image bytes to the GroupMe Image Service and returns the URL.
    """
    try:
        files = {'file': image_bytes}  # The key "file" is required by the GroupMe API
        response = requests.post(IMAGE_SERVICE_URL, files=files)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        return data.get("payload")  # The image URL is in the "payload" field
    except requests.exceptions.RequestException as e:
        print(f"Error uploading image to GroupMe: {e}")
        return None
    

def get_chat_history_from_firestore(collection_name):
    """
    Retrieves the entire chat history from Firestore for a given group and formats it for Gemini
    """
    chat_history = []
    try:
        # Reference to the collection
        messages_ref = db.collection(collection_name)

        # Retrieve all documents in the collection, ordered by timestamp
        docs = messages_ref.order_by("timestamp").get()

        # Iterate over the documents and append them to the history list
        for doc in docs:
            message_data = doc.to_dict()
            message = message_data.get("message", "")
            sender_type = message_data.get("sender type", "")
            sender_name = message_data.get("sender name", "Unknown")
            timestamp = message_data.get("timestamp")

            # Determine the role based on sender type
            if sender_type == "user":
                role = "user"
            elif sender_type == "bot":
                role = "model" # Use model role for bot responses
            else:
                role = "user"

            # Format each entry to contain name, message, and whether the sender is a bot
            formatted_data = Content(
                                    parts=[Part(text=f"{timestamp} - From {sender_name} : {message} ")],
                                    role=role)
            chat_history.append(formatted_data)

    except Exception as e:
        print(f"Error retrieving chat history from Firestore: {e}")
    return chat_history

def run_admin_tests(message_text):
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




@app.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint for Google Cloud
    """
    return "OK", 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))