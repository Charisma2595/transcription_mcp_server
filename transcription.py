import os
import json
import logging
import sys
import fire
from datetime import datetime
from typing import Any
import assemblyai as aai
from mcp.server.fastmcp import FastMCP

# Configure logging
def setup_logging():
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    log_file = os.path.join(logs_dir, f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# Get API key from environment variable
api_key = os.getenv("API_KEY")
if not api_key:
    logger.error("No API key provided. Set it using API_KEY environment variable")
    sys.exit(1)

# Initialize AssemblyAI with the API key
try:
    aai.settings.api_key = api_key
    logger.info("AssemblyAI client initialized with API key")
except Exception as e:
    logger.error(f"Failed to initialize AssemblyAI client: {str(e)}")
    sys.exit(1)

# Create MCP server
mcp = FastMCP(name="Audio Transcription Service")

TRANSCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "transcripts")

def ensure_dir():
    if not os.path.exists(TRANSCRIPTS_DIR):
        os.makedirs(TRANSCRIPTS_DIR)
        logger.info(f"Created transcripts directory at {TRANSCRIPTS_DIR}")

def format_transcript(transcript: Any) -> dict[str, Any]:
    """Format an AssemblyAI transcript into a JSON-compatible dictionary."""
    return {
        "text": transcript.text,
        "words": [
            {
                "text": word.text,
                "start": word.start,
                "end": word.end,
                "confidence": word.confidence,
                "speaker": word.speaker,
                "channel": None
            } for word in transcript.words
        ],
        "audio_duration": transcript.audio_duration,
        "status": transcript.status.value
    }

@mcp.tool()
def transcribe_audio(file_path: str) -> str:
    """
    Transcribe an MP3 audio file using AssemblyAI and save the transcript as JSON.

    Args:
        file_path: Path to the MP3 audio file to transcribe.

    Returns:
        Confirmation message with the path to the saved JSON transcript or an error message.
    """
    ensure_dir()
    
    # Validate file existence and extension
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return f"Error: File {file_path} does not exist."
    if not file_path.lower().endswith('.mp3'):
        logger.error(f"Invalid file format: {file_path}")
        return "Error: Only MP3 files are supported."
    
    logger.info(f"Starting transcription of {file_path}")
    
    config = aai.TranscriptionConfig(
        speech_model=aai.SpeechModel.best,
        speaker_labels=True
    )
    
    try:
        # Transcribe the audio file
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(file_path, config=config)
        
        if transcript.status == aai.TranscriptStatus.error:
            logger.error(f"Transcription failed: {transcript.error}")
            return f"Error: Transcription failed - {transcript.error}"
        
        logger.info("Transcription completed successfully")
        
        # Format and save JSON transcript
        transcript_data = format_transcript(transcript)
        output_file = os.path.join(TRANSCRIPTS_DIR, f"transcript_{os.path.basename(file_path)}.json")
        with open(output_file, "w") as f:
            json.dump(transcript_data, f, indent=2)
        
        logger.info(f"Transcript saved to {output_file}")
        return f"Transcript saved to {output_file}!"
        
    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}", exc_info=True)
        return f"Error: An unexpected error occurred - {str(e)}"

if __name__ == "__main__":
    logger.info("Starting MCP server...")
    logger.info(f"Current working directory: {os.getcwd()}")
    mcp.run()

    if len(sys.argv) > 1:
        def list_transcripts():
            ensure_dir()
            return [f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith(".json")]

        fire.Fire({
            "transcribe": transcribe_audio,
            "list": list_transcripts
        })