# Transcription MCP Sever

An MCP (Model-Context-Protocol) server for transcribing MP3 audio files using the AssemblyAI API. This server provides command-line and Docker-based tools to transcribe audio. this application can be use by Podcasters, Content Creator, Educators and Business Teams making thier task more easier.


## Features

- Accepts .mp3 files via command-line interface using Fire
- Transcribe MP3 audio files into JSON transcripts using AssemblyAI API
- Speaker diarization (speaker labels) enabled
- Save transcripts in a local "transcripts/" directory
- Easy-to-use command-line interface 
- ready to run in a Docker container for portability and deployment


## System Architecture Overview

This application is a microservice designed to transcribe audio files using AssemblyAI.

### Architecture Breakdown
- Uvicorn as MCP Server Runtime: Uvicorn runs the server process, acting as the entry point for executing transcription jobs.
- AssemblyAI Client: This component handles all communication with the AssemblyAI API. 
- CLI via Google Fire: The application includes a robust command-line interface built with Google Fire. Users can transcribe audio files directly from the terminal
- Dockerized Environment: While the server can be run directly on a local machine, it also includes a lightweight Docker configuration for users who prefer containerized deployment. 

## Getting started

### Prerequisites
- Python 3.10+ (its Stable, popular, well-supported)
- Uvicorn (Lightweight ASGI server )
- Google Fire (	CLI Framework, Makes CLI creation simple and powerful)
- AssemblyAI API key (API Interface, sign up at https://www.assemblyai.com/)
- Docker (optional, for containerized usage. Ensures consistent, portable deployment)

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd <repo-folder> 
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set your AssemblyAI API key as an environment variable:
```bash
export API_KEY="your_assemblyai_api_key"   # Linux / macOS
set API_KEY="your_assemblyai_api_key"      # Windows CMD
```

## Usage

### Command-line Interface
Run the script 
```bash
uv run transcription.py transcribe path/to/audio.mp3
```

## Docker Usage
Build Docker Image
```bash
docker build -t assemblyai-mcp-server .
```
Run Docker Container
make sure to set or export your api-key as an env using cmd line above.
```bash
docker run -v %cd%:/app -e API_KEY="" audio-transcriber transcribe " path/to/audio.mp3"
```