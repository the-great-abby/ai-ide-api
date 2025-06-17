FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY . .
COPY ../utils ./utils
RUN pip install pika requests
CMD ["python", "main.py"] 