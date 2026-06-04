"""
Transcription Service

Provides speech-to-text transcription using Groq Whisper API.
Replaces browser-based SpeechRecognition with production-grade server-side transcription.
"""

import tempfile
from pathlib import Path

from app.core.config import settings

def transcribe_audio(audio_data: bytes, filename: str = "audio.webm") -> str:
    """
    Transcribe audio using Groq Whisper API.
    
    Args:
        audio_data: Raw audio file bytes
        filename: Original filename (used to determine format)
        
    Returns:
        Transcribed text
        
    Raises:
        ValueError: If API key is not configured or audio is invalid
        Exception: If transcription fails
    """
    # Validate API key
    if not settings.llm_provider_api_key:
        raise ValueError("Groq API key is not configured. Set LLM_PROVIDER_API_KEY in .env")
    
    # Validate audio data
    if not audio_data or len(audio_data) == 0:
        raise ValueError("Audio data is empty")
    
    # Check file size (Groq has a 25MB limit)
    max_size = 25 * 1024 * 1024  # 25MB
    if len(audio_data) > max_size:
        raise ValueError(f"Audio file too large. Maximum size is 25MB, got {len(audio_data) / 1024 / 1024:.2f}MB")
    
    try:
        # Import OpenAI client (Groq uses OpenAI-compatible API)
        try:
            from openai import OpenAI
        except ImportError:
            raise ValueError("OpenAI library is not installed. Run: pip install openai")
        
        # Initialize Groq client
        client = OpenAI(
            api_key=settings.llm_provider_api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        
        print(f"[DEBUG] Transcribing audio file: {filename} ({len(audio_data)} bytes)")
        
        # Create temporary file for audio
        # Groq Whisper supports: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, webm
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        try:
            # Open file and send to Groq Whisper
            with open(temp_file_path, "rb") as audio_file:
                # Use Whisper large v3 model (most accurate)
                transcription = client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=audio_file,
                    response_format="text"
                )
            
            # Extract transcript
            if isinstance(transcription, str):
                transcript = transcription
            else:
                transcript = transcription.text if hasattr(transcription, 'text') else str(transcription)
            
            transcript = transcript.strip()
            
            if not transcript:
                raise ValueError("Transcription returned empty text")
            
            print(f"[DEBUG] Transcription successful: {len(transcript)} characters")
            return transcript
            
        finally:
            # Clean up temporary file
            try:
                Path(temp_file_path).unlink()
            except Exception as e:
                print(f"[WARNING] Failed to delete temp file: {e}")
    
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Transcription failed: {error_msg}")
        print(f"[ERROR] Error type: {type(e).__name__}")
        
        # Provide user-friendly error messages
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            raise ValueError(f"API key error: {error_msg}. Please check your Groq API key.")
        elif "rate_limit" in error_msg.lower():
            raise ValueError("Rate limit exceeded. Please try again in a moment.")
        elif "model" in error_msg.lower():
            raise ValueError(f"Model error: {error_msg}. Whisper model may not be available.")
        elif "file" in error_msg.lower() or "format" in error_msg.lower():
            raise ValueError(f"Audio format error: {error_msg}. Supported formats: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, webm")
        else:
            raise Exception(f"Transcription failed: {error_msg}")


# Made with Bob