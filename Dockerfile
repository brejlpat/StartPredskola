FROM python:3.11-slim

WORKDIR /app

# kopíruj requirements zvlášť, kvůli layer cache
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# pak teprve zbytek aplikace
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
