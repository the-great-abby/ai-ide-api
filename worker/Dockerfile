FROM python:3.11-slim
WORKDIR /app
COPY main.py .
RUN pip install pika requests
CMD ["python", "main.py"] 