FROM python:3.10-slim-buster

WORKDIR /gemini-bot-app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "app.py"]
CMD gunicorn -b :$PORT main:app