FROM python:3.10-slim

WORKDIR /app


COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

# Create transcripts directory
RUN mkdir -p transcripts


ENTRYPOINT ["python", "transcription.py"] 