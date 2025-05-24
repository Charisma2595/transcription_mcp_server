from mcp.server.fastmcp import FastMCP
import os
import assemblyai as aai
import sys
import logging
import json
from datetime import datetime

# Configure logging
def setup_logging():
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    log_file = os.path.join(logs_dir, f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  
        ]
    )
    return logging.getLogger(__name__)

# Initialize logger
logger = setup_logging()


# Get API key from environment variable
api_key = os.getenv("API_KEY")
if not api_key:
    logger.error("No API key provided. Set it using API_KEY environment variable")
    sys.exit(1)

try:
    aai.settings.api_key = api_key
    logger.info("AssemblyAI client initialized with API key")
except Exception as e:
    logger.error(f"Failed to initialize AssemblyAI client: {str(e)}")
    sys.exit(1)

# Create an MCP server
mcp = FastMCP("Audio Transcription Service")

TRANSCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "transcripts")

def ensure_dir():
    if not os.path.exists(TRANSCRIPTS_DIR):
        os.makedirs(TRANSCRIPTS_DIR)
        logger.info(f"Created transcripts directory at {TRANSCRIPTS_DIR}")

@mcp.tool()
def transcribe_audio(file_path: str) -> str:
    """
    Transcribe an MP3 audio file using AssemblyAI and save the transcript as JSON.

    Args:
        file_path (str): Path to the MP3 audio file to transcribe.

    Returns:
        str: Confirmation message with the path to the saved JSON transcript.
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
        
        # Prepare JSON output
        transcript_data = {
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
        
        # Save JSON transcript
        output_file = os.path.join(TRANSCRIPTS_DIR, f"transcript_{os.path.basename(file_path)}.json")
        with open(output_file, "w") as f:
            json.dump(transcript_data, f, indent=2)
        
        logger.info(f"Transcript saved to {output_file}")
        return f"Transcript saved to {output_file}!"
        
    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}", exc_info=True)
        return f"Error: An unexpected error occurred - {str(e)}"

@mcp.tool()
def list_transcripts() -> str:
    """
    List all saved JSON transcripts in the transcripts directory.

    Returns:
        str: List of transcript filenames or a message if none exist.
    """
    ensure_dir()
    transcripts = [f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith('.json')]
    logger.info(f"Found {len(transcripts)} transcript(s)")
    return "\n".join(transcripts) or "No transcripts yet."

if __name__ == "__main__":
    logger.info("Starting MCP server...")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # Check if running in an MCP context
    if os.getenv("MCP_MODE", "").lower() == "true":
        logger.info("Running in MCP mode")
        mcp.run()  
    else:
        logger.info("Running in CLI mode")
        import fire
        fire.Fire({
            "transcribe": transcribe_audio,
            "list": list_transcripts
        })