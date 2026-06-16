"""Speech-to-text transcription using an independently configured provider."""

import tempfile
from pathlib import Path

from app.core.config import settings
from app.ai.provider_utils import (
    ProviderConfigurationError,
    ProviderRequestError,
    provider_failure_message,
    run_with_retries,
)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def _get_openai_client_class():
    from openai import OpenAI

    return OpenAI

# Language code mapping for Whisper API
# Whisper uses ISO 639-1 codes
SUPPORTED_LANGUAGES = {
    "en": "en",  # English
    "hi": "hi",  # Hindi
    "es": "es",  # Spanish
    "fr": "fr",  # French
    "de": "de",  # German
    "ja": "ja"   # Japanese
}

def transcribe_audio(audio_data: bytes, filename: str = "audio.webm", language: str = "en") -> str:
    """
    Transcribe audio using Groq Whisper API with language support.
    
    Args:
        audio_data: Raw audio file bytes
        filename: Original filename (used to determine format)
        language: ISO 639-1 language code (en, hi, es, fr, de, ja)
        
    Returns:
        Transcribed text
        
    Raises:
        ValueError: If audio is invalid
        AIProviderError: If provider config or request fails
    """
    # Validate audio data
    if not audio_data or len(audio_data) == 0:
        raise ValueError("Audio data is empty")
    
    # Check file size (Groq has a 25MB limit)
    max_size = 25 * 1024 * 1024  # 25MB
    if len(audio_data) > max_size:
        raise ValueError(f"Audio file too large. Maximum size is 25MB, got {len(audio_data) / 1024 / 1024:.2f}MB")
    
    provider = settings.transcription_provider.lower()
    if provider == "disabled":
        raise ProviderConfigurationError(
            "Transcription provider is not configured.",
            provider=provider
        )
    if provider not in {"openai", "groq"}:
        raise ProviderConfigurationError(
            "Unsupported transcription provider configured.",
            provider=provider
        )
    if not settings.transcription_provider_api_key:
        raise ProviderConfigurationError(
            "Transcription provider is not configured.",
            provider=provider
        )

    try:
        OpenAI = _get_openai_client_class()
    except ImportError as exc:
        raise ProviderConfigurationError(
            "OpenAI-compatible client is not installed.",
            provider=provider
        ) from exc

    base_url = settings.transcription_provider_base_url
    if provider == "groq" and not base_url:
        base_url = GROQ_BASE_URL

    client_kwargs = {
        "api_key": settings.transcription_provider_api_key,
        "timeout": settings.transcription_timeout_seconds,
        "max_retries": 0
    }
    if base_url:
        client_kwargs["base_url"] = base_url

    client = OpenAI(**client_kwargs)

    # Groq/OpenAI Whisper supports: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, webm.
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
        temp_file.write(audio_data)
        temp_file_path = temp_file.name
        
    try:
        def operation() -> str:
            with open(temp_file_path, "rb") as audio_file:
                whisper_language = SUPPORTED_LANGUAGES.get(language, "en")
                language_names = {
                    "en": "English",
                    "hi": "Hindi",
                    "es": "Spanish",
                    "fr": "French",
                    "de": "German",
                    "ja": "Japanese"
                }
                prompt_text = f"Transcribe this audio in {language_names.get(language, 'English')}. Do not translate."

                transcription = client.audio.transcriptions.create(
                    model=settings.transcription_model_name,
                    file=audio_file,
                    response_format="text",
                    language=whisper_language,
                    prompt=prompt_text
                )

            if isinstance(transcription, str):
                transcript = transcription
            else:
                transcript = transcription.text if hasattr(transcription, 'text') else str(transcription)

            transcript = transcript.strip()
            if not transcript:
                raise ProviderRequestError(
                    provider_failure_message("Transcription provider"),
                    provider=provider
                )
            return transcript

        return run_with_retries(
            operation,
            provider=provider,
            attempts=settings.transcription_max_retries + 1,
            public_message=provider_failure_message("Transcription provider")
        )
    finally:
        try:
            Path(temp_file_path).unlink(missing_ok=True)
        except OSError:
            pass


# Made with Bob
