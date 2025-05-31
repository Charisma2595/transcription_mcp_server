import asyncio
import os
import sys
from contextlib import AsyncExitStack
from typing import Any, Optional

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables from .env file (if it exists)
load_dotenv()

class MCPTranscriptionClient:
    """Client for interacting with the AssemblyAI-based MCP transcription server."""

    def __init__(self):
        """Initialize the transcription MCP client."""
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.stdio: Optional[Any] = None
        self.protocol: Optional[Any] = None

    async def connect_to_server(self, server_script_path: str = r"mcp\server_transcription.py"):
        """Connect to the MCP transcription server.

        Args:
            server_script_path: Path to the server_transcription.py script.
        """
        # Ensure the server script exists
        if not os.path.exists(server_script_path):
            print(f"Error: Server script not found at {server_script_path}")
            raise FileNotFoundError(f"Server script not found: {server_script_path}")

        # Get API key from environment
        api_key = os.getenv("API_KEY")
        if not api_key:
            print("Error: API_KEY environment variable not set. Set it using 'set API_KEY=your_key' in the command prompt.")
            raise ValueError("API_KEY environment variable not set.")

        # Server configuration with explicit API_KEY in environment
        env = os.environ.copy()
        env["API_KEY"] = api_key
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
            env=env
        )

        # Connect to the server with a timeout
        try:
            async with asyncio.timeout(10):
                stdio_transport = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                self.stdio, self.protocol = stdio_transport
                self.session = await self.exit_stack.enter_async_context(
                    ClientSession(self.stdio, self.protocol)
                )

                
                await self.session.initialize()

                # List available tools
                tools_result = await self.session.list_tools()
                print("\nConnected to Audio Transcription Service with tools:")
                for tool in tools_result.tools:
                    print(f"  - {tool.name}: {tool.description}")
        except TimeoutError:
            print("Error: Connection to server timed out. Ensure server_transcription.py is running and API_KEY is valid.")
            raise
        except Exception as e:
            print(f"Error connecting to server: {str(e)}")
            raise

    async def transcribe_audio(self, file_path: str) -> str:
        """Transcribe an audio file using the MCP server.

        Args:
            file_path: Path to the MP3 audio file to transcribe.

        Returns:
            The transcription result or error message.
        """
        if not self.session:
            raise RuntimeError("Client is not connected to the server. Call connect_to_server first.")

        # Normalize and validate file path
        file_path = os.path.normpath(file_path.strip())
        if not os.path.exists(file_path):
            return f"Error: Audio file not found at '{file_path}'. Ensure the path is correct and the file exists."
        if not file_path.lower().endswith('.mp3'):
            return f"Error: File '{file_path}' is not an MP3 file. Only MP3 files are supported."

        # Directly call the transcribe_audio tool
        try:
            async with asyncio.timeout(60):  
                result = await self.session.call_tool(
                    "transcribe_audio",
                    arguments={"file_path": file_path}
                )
                return result.content[0].text
        except TimeoutError:
            return "Error: Transcription timed out. The audio file may be too large or the server may be unresponsive."
        except Exception as e:
            return f"Error during transcription: {str(e)}. Check your internet connection, API key, and server logs for details."

    async def cleanup(self):
        """Clean up resources."""
        await self.exit_stack.aclose()

async def main(audio_file: str):
    """Main entry point for the client.

    Args:
        audio_file: Path to the MP3 audio file to transcribe.
    """
    client = MCPTranscriptionClient()
    try:
        await client.connect_to_server(r"mcp\server_transcription.py")

        # Transcribe the audio file
        print(f"\nTranscribing audio file: {audio_file}")
        response = await client.transcribe_audio(audio_file)
        print(f"\nTranscription Response: {response}")

    except Exception as e:
        print(f"Error in main: {str(e)}")
    finally:
        # Clean up
        await client.cleanup()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: No audio file path provided. Usage: python mcp\\client_transcription.py \"<audio_file_path>\"")
        print("Example: python mcp\\client_transcription.py \"C:\\Users\\HomePC\\Desktop\\mcp_task2\\test_audios\\Voicy_Happiness can always be found.mp3\"")
        sys.exit(1)

    audio_file = sys.argv[1].strip()
    asyncio.run(main(audio_file))