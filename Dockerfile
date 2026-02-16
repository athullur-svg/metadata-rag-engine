FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV SCHEMADOC_INDEX=/app/.local/index
EXPOSE 8000

CMD ["uvicorn", "metadata_rag_engine.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
