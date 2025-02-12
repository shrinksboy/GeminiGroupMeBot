# client = genai.Client(api_key="AIzaSyDJDntH8438Nmv8Ywja-W0gNZ9oH4q06w8")
# response = client.models.generate_content(
#     model="gemini-2.0-flash", contents="give me a haiku about cookies"
# )
# print(response.text)

import os

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    """Example Hello World route."""
    name = os.environ.get("NAME", "World")
    return f"Goodbye {name}!"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

