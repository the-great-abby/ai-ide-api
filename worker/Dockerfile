FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY . .
COPY worker/ ./worker
COPY ../utils ./utils
COPY ../scripts ./scripts
RUN pip install -r worker/requirements.txt
ENV PYTHONPATH=/app:/app/scripts:/app/utils:/app/worker
RUN pip install pika requests
CMD ["python", "main.py"] 