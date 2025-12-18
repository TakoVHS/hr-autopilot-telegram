FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY backend/ .

RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
