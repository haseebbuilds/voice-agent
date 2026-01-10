import httpx
from config.settings import settings
from typing import Optional


async def generate_speech(text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM") -> Optional[str]:
    if not settings.ELEVENLABS_API_KEY:
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": settings.ELEVENLABS_API_KEY
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            response = await client.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                return None
            
            return None
            
    except Exception as e:
        print(f"Error generating speech: {e}")
        return None


def generate_twiml_say(text: str) -> str:
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    
    return f'<Say voice="alice">{text}</Say>'

