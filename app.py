# client = genai.Client(api_key="AIzaSyDJDntH8438Nmv8Ywja-W0gNZ9oH4q06w8")
# response = client.models.generate_content(
#     model="gemini-2.0-flash", contents="give me a haiku about cookies"
# )
# print(response.text)

import os

from google import genai

from flask import Flask, request, jsonify

import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# @app.route('/', methods=['POST'])
# def webhook_handler():
#     """
#     Handles incoming POST requests from the V3 message provider.
#     """
#     logger.info("Received request from webhook.")

#     try:
#         # Extract data from the request (assuming JSON format)
#         data = request.get_json()

#         # Process the V3 message (Implement your logic here)
#         v3_message = data.get('message', None)  # Adjust the key as needed
#         if v3_message:
#             logger.info(f"Received V3 message: {v3_message}")
#             # Your logic to process the message goes here.
#             # Example:
#             response_message = process_message(v3_message)  # Call a function to handle the processing
#         else:
#             logger.warning("No 'message' field found in the request.")
#             return jsonify({"status": "error", "message": "Missing 'message' field"}), 400 # Bad Request

#         # Create a response
#         response_data = {
#             "status": "success",
#             "response": response_message
#         }
#         logger.info(f"Sending response: {response_data}")
#         return jsonify(response_data), 200  # OK

#     except Exception as e:
#         logger.error(f"Error processing request: {e}")
#         return jsonify({"status": "error", "message": str(e)}), 500  # Internal Server Error

@app.route("/")
def hello_world():
    """Example Hello World route."""
    name = os.environ.get("NAME", "World")
    return f"Hello {name}!"


# def process_message(v3_message):
#     """
#     Processes the V3 message (GroupMe message) and generates a response.
#     """

#     try:
#         # Extract relevant information from the message
#         sender_name = v3_message.get("name", "Unknown Sender")  # Get sender name, default to "Unknown Sender"
#         message_text = v3_message.get("text", "")  # Get message text, default to empty string
#         group_id = v3_message.get("group_id", "Unknown Group")
#         sender_id = v3_message.get("sender_id", "Unknown Sender ID")

#         # Build a response based on the extracted information
#         response_text = f"Received message from {sender_name} (sender ID: {sender_id}) in group {group_id}: '{message_text}'"

#         # Add your custom logic here to process the message further.
#         # For example, you could:
#         #   - Check if the message contains specific keywords.
#         #   - Perform an action based on the message content.
#         #   - Interact with other APIs.

#         #Example action - if the text contains "test", return "test successful"
#         if "test" in message_text.lower():
#             response_text = "Test successful"

#         return response_text

#     except Exception as e:
#         logger.error(f"Error processing message: {e}")
#         return f"Error processing message: {e}"  # Return an error message to the webhook caller


# @app.route('/health', methods=['GET'])
# def health_check():
#     """
#     Simple health check endpoint for Google Cloud.  Useful for auto-scaling and monitoring.
#     """
#     return "OK", 200


if __name__ == '__main__':
    # Don't use this in production.  Gunicorn will handle the serving.
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))