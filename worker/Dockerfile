FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY . .
COPY utils ./utils
COPY scripts ./scripts
RUN pip install -r requirements.txt
ENV PYTHONPATH=/app:/app/scripts:/app/utils
RUN pip install pika requests
CMD ["python", "worker/main.py"] 