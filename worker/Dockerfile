FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY worker/ .
COPY requirements.txt .
RUN pip install -r requirements.txt
CMD ["python", "main.py"] 