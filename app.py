# client = genai.Client(api_key=GOOGLE_API_KEY)
# response = client.models.generate_content(
#     model="gemini-2.0-flash", contents="give me a haiku about cookies"
# )
# print(response.text)

################################################################################################################################


# import os

# from flask import Flask

# app = Flask(__name__)


# @app.route("/")
# def hello_world():
#     """Example Hello World route."""
#     name = os.environ.get("NAME", "World")
#     return f"Goodbye cruel {name}!"


# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


################################################################################################################################


import http
from flask import Flask, request, jsonify
import logging
import os
import requests

app = Flask(__name__)

# Load environment variables
BOT_ID = os.environ.get("BOT_ID")  # Get your bot ID from the environment
GROUPME_API_URL = "https://api.groupme.com/v3/bots/post"  # GroupMe API endpoint

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    Processes the V3 message (GroupMe message) and generates a response.
    """

    try:
        # Extract relevant information from the message
        sender_name = v3_message.get("name", "Unknown Sender")  # Get sender name, default to "Unknown Sender"
        message_text = v3_message.get("text", "")  # Get message text, default to empty string
        group_id = v3_message.get("group_id", "Unknown Group")
        sender_id = v3_message.get("sender_id", "Unknown Sender ID")

        # Build a response based on the extracted information

        # Status test
        if "bot-status-test" in message_text.lower():
            response_text = "Test successful"
            response_text = "ye"

        # Check if response needs to be sent back
        if message_text.lower().startswith("@chatius"):
             response_text = "Greetings human"
             response_payload = {
                  "bot_id": BOT_ID,
                "text": response_text
             }
             send_response(response_payload)

        

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return f"Error processing message: {e}"  # Return an error message to the webhook caller
    
    
def send_response(response_payload):
    """
    Send POST response to groupme
    """
    try:
            response = requests.post(GROUPME_API_URL, json=response_payload)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            logger.info(f"Successfully sent message to GroupMe. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
            logger.error(f"Error sending message to GroupMe: {e}")
            return f"Error sending message to GroupMe: {e}"

    return "Message sent to GroupMe."  # success message



@app.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint for Google Cloud.  Useful for auto-scaling and monitoring.
    """
    return "OK", 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))