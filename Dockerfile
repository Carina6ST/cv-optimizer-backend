FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Ensure spaCy model exists
RUN python - <<'PY'
import importlib.util, sys
m='en_core_web_sm'
import spacy
sys.exit(0) if importlib.util.find_spec(m) else spacy.cli.download(m)
PY

COPY . /app

EXPOSE 8000

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app:app", "-b", "0.0.0.0:8000", "-w", "2", "--timeout", "120"]
