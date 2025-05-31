import asyncio
import os
import sys
from contextlib import AsyncExitStack
from typing import Any, Optional

from mcp import ClientSession
from mcp.client.sse import sse_client

class MCPTranscriptionClient:
    """Client for interacting with the AssemblyAI-based MCP transcription server."""

    def __init__(self):
        """Initialize the transcription MCP client."""
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(self, server_url: str = "http://localhost:8050/sse"):
        """Connect to the MCP transcription server using SSE.

        Args:
            server_url: URL of the MCP server (SSE endpoint).
        """
        # Connect to the server with a timeout
        try:
            async with asyncio.timeout(10):  
                sse_transport = await self.exit_stack.enter_async_context(
                    sse_client(server_url)
                )
                read_stream, write_stream = sse_transport
                self.session = await self.exit_stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )

                # Initialize the connection
                await self.session.initialize()

               
                tools_result = await self.session.list_tools()
                print("\nConnected to Audio Transcription Service with tools:")
                for tool in tools_result.tools:
                    print(f"  - {tool.name}: {tool.description}")
        except TimeoutError:
            print("Error: Connection to server timed out. Ensure the server is running on port 8050 and accessible.")
            raise
        except Exception as e:
            print(f"Error connecting to server: {str(e)}")
            raise

    async def transcribe_audio(self, file_path: str) -> str:
        """Transcribe an audio file using the MCP server.

        Args:
            file_path: Path to the MP3 audio file to transcribe (Windows path).

        Returns:
            The transcription result or error message.
        """
        if not self.session:
            raise RuntimeError("Client is not connected to the server. Call connect_to_server first.")

        # Validate file existence locally
        print(f"Checking host path: {file_path}") 
        if not os.path.exists(file_path):
            return f"Error: Audio file not found at '{file_path}' on the host. Ensure the path is correct."
        if not file_path.lower().endswith('.mp3'):
            return f"Error: File '{file_path}' is not an MP3 file. Only MP3 files are supported."

        # Convert Windows path to container path
        # Example: C:\Users\HomePC\Music\my_audio.mp3 -> /mnt/users/HomePC/Music/my_audio.mp3
        container_path = file_path
        if file_path[1:3] == ':\\':  
            # Remove drive letter and convert to container path
            parts = file_path.split(':', 1)
            rest = parts[1].lstrip('\\/')  
            if rest.startswith('Users\\') or rest.startswith('Users/'):
                rest = rest[len('Users\\'):] 
            container_path = f"/mnt/users/{rest}"
        container_path = container_path.replace('\\', '/')
        container_path = os.path.normpath(container_path).replace('\\', '/')
        print(f"Container path: {container_path}")  

        # Call the transcribe_audio tool with container path
        try:
            async with asyncio.timeout(60):  
                result = await self.session.call_tool(
                    "transcribe_audio",
                    arguments={"file_path": container_path}
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
        await client.connect_to_server()

        # Transcribe the audio file
        print(f"\nTranscribing audio file: {audio_file}")
        response = await client.transcribe_audio(audio_file)
        print(f"\nTranscription Response: {response}")

    except Exception as e:
        print(f"Error in main: {str(e)}")
    finally:
       
        await client.cleanup()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: No audio file path provided. Usage: python client.py \"<audio_file_path>\"")
        print("Example: python client.py \"C:\\Users\\HomePC\\Music\\my_audio.mp3\"")
        sys.exit(1)

    audio_file = sys.argv[1].strip()
    asyncio.run(main(audio_file))