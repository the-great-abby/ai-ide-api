FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["uvicorn", "rule_api_server:app", "--host", "0.0.0.0", "--reload"] 