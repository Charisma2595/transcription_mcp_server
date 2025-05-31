FROM python:3.12-slim

WORKDIR /app


RUN pip install uv


COPY requirements.txt .


RUN uv venv
RUN uv pip install -r requirements.txt

# Copy application code
COPY run_with_docker/server.py .
COPY run_with_docker/client.py .


RUN mkdir -p /app/transcripts /app/logs

# Expose the port the server runs on
EXPOSE 8050


CMD ["uv", "run", "server.py"]