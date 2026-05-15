FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x certs/generate_certs.sh && ./certs/generate_certs.sh
RUN python init_db.py

EXPOSE 5000

CMD ["python", "-m", "server.main"]
