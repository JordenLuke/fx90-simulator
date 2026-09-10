FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY scripts ./scripts
COPY data ./data
COPY scenarios ./scenarios
RUN mkdir -p /app/certs

ENV PYTHONPATH=/app/src

EXPOSE 443

CMD ["python", "-m", "fx90_simulator"]
