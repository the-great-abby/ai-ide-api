FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# EXPOSE 8000 is for internal container use; 9103 is mapped as the standard dev port in docker-compose
EXPOSE 8000

# Copy the AI rule proposal bot script into the container
COPY auto_code_review.py /app/auto_code_review.py

CMD ["uvicorn", "rule_api_server:app", "--host", "0.0.0.0", "--reload"] 