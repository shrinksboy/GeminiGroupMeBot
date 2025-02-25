
from google.genai.types import GenerateContentConfig
from google import genai
from google.genai.types import Content, HttpOptions, Part


GOOGLE_API_KEY = "AIzaSyDJDntH8438Nmv8Ywja-W0gNZ9oH4q06w8"

client = genai.Client(api_key=GOOGLE_API_KEY)


     # System Instructions for gemini
sys_instruct = "You are a chatbot in a GroupMe group chat. Your name is Chatius."


# Create History
chat_history = []
user_message = Content(
            parts=[Part(text="Hello, my name is Jonah")],
            role="user")
bot_response = Content(parts=[Part(text="Nice to meet you Jonah")], role="model")

chat_history.append(user_message)
chat_history.append(bot_response)

print(chat_history)

chat = client.chats.create(model="gemini-2.0-flash",
                           history=chat_history,
                        config=GenerateContentConfig(system_instruction=sys_instruct),
                        )

response = chat.send_message("What is my name?")
print(response.text)

response = chat.send_message("What is your name?")
print(response.text)

print(chat._curated_history)
