import requests
import base64
import logging

log = logging.getLogger("jarvis.tts")

# Your ElevenLabs API key
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")  # Replace with your key
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice

async def synthesize_speech(text: str) -> bytes | None:
    """Generate speech using ElevenLabs API"""
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=15)
        
        if response.status_code == 200:
            log.info(f"ElevenLabs TTS success: {len(response.content)} bytes")
            return response.content
        else:
            log.error(f"ElevenLabs error: {response.status_code} - {response.text[:100]}")
            return None
    except Exception as e:
        log.error(f"TTS error: {e}")
        return None
