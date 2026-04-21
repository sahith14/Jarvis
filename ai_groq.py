import os
from groq import Groq
import logging

log = logging.getLogger("jarvis.ai")

# Your Groq API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

_client = None

def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client

async def generate_response(prompt: str, system_prompt: str = "", history: list = None) -> str:
    """Generate response using Groq's free API"""
    client = get_client()
    if not client:
        return "I'm having trouble connecting to my systems, sir."
    
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history[-10:])
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-versatile",
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        log.error(f"Groq error: {e}")
        return f"Apologies, sir. Having trouble with my language systems."
