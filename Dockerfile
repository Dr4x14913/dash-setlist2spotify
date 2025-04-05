# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=8050
EXPOSE 8050

CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "1", "app:server"]