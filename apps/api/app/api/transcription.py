"""
Transcription API Endpoint

Provides speech-to-text transcription using Groq Whisper API.
"""

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.ai.provider_utils import AIProviderError
from app.ai.transcription_service import transcribe_audio

router = APIRouter(prefix="/transcribe", tags=["transcription"])


class TranscriptionResponse(BaseModel):
    """Response model for transcription endpoint."""
    transcript: str


@router.post("", response_model=TranscriptionResponse)
async def transcribe_audio_file(
    file: UploadFile = File(...),
    language: str = "en"
) -> TranscriptionResponse:
    """
    Transcribe audio file to text using Groq Whisper with language support.
    
    Accepts audio files in formats: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, webm
    Maximum file size: 25MB
    
    Args:
        file: Audio file to transcribe
        language: ISO 639-1 language code (en, hi, es, fr, de, ja). Default: en
        
    Returns:
        TranscriptionResponse with transcript text
        
    Raises:
        400: Invalid audio file or format
        503: Transcription service unavailable
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Check file extension
    supported_formats = {".flac", ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".ogg", ".wav", ".webm"}
    file_ext = file.filename.lower().split(".")[-1] if "." in file.filename else ""
    
    if f".{file_ext}" not in supported_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio format: {file_ext}. Supported formats: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, webm"
        )
    
    try:
        # Read audio data
        audio_data = await file.read()
        
        if not audio_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file is empty"
            )
        
        # Transcribe using Groq Whisper with language support
        transcript = transcribe_audio(audio_data, file.filename, language)
        
        return TranscriptionResponse(transcript=transcript)
        
    except ValueError as exc:
        # Client errors (invalid input, missing API key, etc.)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc
    except AIProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.public_message
        ) from exc


# Made with Bob
