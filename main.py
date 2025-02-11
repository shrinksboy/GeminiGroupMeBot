from google import genai

client = genai.Client(api_key="AIzaSyDJDntH8438Nmv8Ywja-W0gNZ9oH4q06w8")
response = client.models.generate_content(
    model="gemini-2.0-flash", contents="tell me a joke"
)
print(response.text)