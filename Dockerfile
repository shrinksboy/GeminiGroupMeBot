FROM python:3.10-slim-buster

WORKDIR /gemini-bot-app-dev

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Force Docker to invalidate the cache:
RUN echo "Invalidate cache" > invalidate.txt
COPY app.py .

ENV PORT 8080

# CMD ["python3", "app.py"]
CMD gunicorn -b :$PORT app:app

################################### TEST BELOW

# FROM python:3.9-slim-buster

# WORKDIR /app

# COPY requirements.txt .
# RUN pip install -r requirements.txt

# # Force Docker to invalidate the cache:
# RUN echo "Invalidate cache" > invalidate.txt

# COPY testapp.py .

# ENV PORT 8080

# CMD gunicorn -b :$PORT testapp:app