FROM ubuntu:22.04

RUN apt update -y && apt install -y python3 python3-pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src .
COPY .env .