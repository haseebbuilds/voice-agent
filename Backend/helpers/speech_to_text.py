import httpx
from config.settings import settings
from typing import Optional


async def transcribe_audio(audio_url: str) -> Optional[str]:
    """
    Transcribe audio from Twilio using Deepgram API
    
    Args:
        audio_url: URL of the audio file from Twilio
        
    Returns:
        Transcribed text or None if failed
    """
    if not settings.DEEPGRAM_API_KEY:
        # Fallback: return None if API key not configured
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            # Download audio from Twilio
            audio_response = await client.get(audio_url)
            audio_data = audio_response.content
            
            # Send to Deepgram for transcription
            headers = {
                "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
                "Content-Type": "audio/wav"
            }
            
            response = await client.post(
                "https://api.deepgram.com/v1/listen",
                headers=headers,
                content=audio_data,
                params={"model": "nova-2", "language": "en-US"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if "results" in result and "channels" in result["results"]:
                    transcripts = result["results"]["channels"][0]["alternatives"]
                    if transcripts:
                        return transcripts[0].get("transcript", "")
            
            return None
            
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None


async def transcribe_twilio_recording(recording_url: str, auth_token: str) -> Optional[str]:
    if not settings.DEEPGRAM_API_KEY:
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            audio_response = await client.get(
                recording_url,
                auth=("", auth_token)
            )
            audio_data = audio_response.content
            
            headers = {
                "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
                "Content-Type": "audio/wav"
            }
            
            response = await client.post(
                "https://api.deepgram.com/v1/listen",
                headers=headers,
                content=audio_data,
                params={"model": "nova-2", "language": "en-US"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if "results" in result and "channels" in result["results"]:
                    transcripts = result["results"]["channels"][0]["alternatives"]
                    if transcripts:
                        return transcripts[0].get("transcript", "")
            
            return None
            
    except Exception as e:
        print(f"Error transcribing Twilio recording: {e}")
        return None

