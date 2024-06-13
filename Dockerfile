
FROM python:3-slim

RUN apt-get update && \
    apt-get install -y gcc python3-dev libffi-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app/

COPY . .

RUN pip3 install --upgrade pip setuptools && \
    pip3 install --no-cache-dir -r requirements.txt

CMD ["bash", "start"]
