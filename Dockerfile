# Backend Dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

EXPOSE 8000

ENV ENVIRONMENT=production
ENV DATABASE_URL=sqlite+aiosqlite:///./montgowork.db

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
