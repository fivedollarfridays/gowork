# Backend Dockerfile
FROM python:3.13-slim

WORKDIR /app

# WeasyPrint (T12.4) requires native Pango/Cairo/FreeType libraries at
# runtime — python:3.13-slim ships without them. Install them before
# pip so the WeasyPrint wheel can load its cffi bindings.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libcairo2 \
        libffi-dev \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

EXPOSE 8000

RUN adduser --disabled-password --gecos "" appuser
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
