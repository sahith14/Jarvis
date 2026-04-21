# whatsapp_agent.py — JARVIS Mark IV WhatsApp Agent
# ══════════════════════════════════════════════════════════════════════════════
# Smart WhatsApp auto-reply with:
# - Priority detection (urgent → 15s, normal → 60s)
# - Tone matching (casual vs formal)
# - Context-based replies
# ══════════════════════════════════════════════════════════════════════════════

import asyncio
from playwright.async_api import async_playwright
import time
import os
import requests
import json

WHATSAPP_DATA_DIR = os.path.abspath("./whatsapp_data")

# Track when we first saw an unread message
# Format: {"Chat Name": {"timestamp": 123456789, "text": "Preview snippet...", "priority": "normal"}}
pending_replies = {}

# ══════════════════════════════════════════════════════════════════════════════
# PRIORITY DETECTION
# ══════════════════════════════════════════════════════════════════════════════

URGENT_KEYWORDS = [
    "urgent", "emergency", "asap", "important", "help",
    "immediately", "now", "quick", "hurry", "critical",
    "need you", "call me", "pick up", "sos",
]

CASUAL_INDICATORS = [
    "lol", "haha", "😂", "🤣", "bruh", "lmao",
    "yo", "sup", "hey", "wassup", "bro", "dude",
    "chill", "nah", "yeah", "yep", "nope",
]

FORMAL_INDICATORS = [
    "sir", "madam", "please", "kindly", "regarding",
    "dear", "respect", "thank you", "would you",
    "could you", "appreciate", "concern",
]

def detect_priority(message: str) -> str:
    """Detect message priority: 'urgent' or 'normal'."""
    msg_lower = message.lower()
    for kw in URGENT_KEYWORDS:
        if kw in msg_lower:
            return "urgent"
    return "normal"

def detect_tone(message: str) -> str:
    """Detect message tone: 'casual', 'formal', or 'neutral'."""
    msg_lower = message.lower()
    casual_score = sum(1 for ind in CASUAL_INDICATORS if ind in msg_lower)
    formal_score = sum(1 for ind in FORMAL_INDICATORS if ind in msg_lower)

    if casual_score > formal_score:
        return "casual"
    elif formal_score > casual_score:
        return "formal"
    return "neutral"


# ══════════════════════════════════════════════════════════════════════════════
# REPLY DELAY BASED ON PRIORITY
# ══════════════════════════════════════════════════════════════════════════════

DELAY_MAP = {
    "urgent": 15,   # 15 seconds for urgent messages
    "normal": 60,   # 60 seconds for normal messages
}


async def run_whatsapp():
    async with async_playwright() as p:
        print("[WHATSAPP] Launching browser...")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=WHATSAPP_DATA_DIR,
            headless=False, # Set to False so the window is visible
            viewport={"width": 1024, "height": 768}
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()
        print("[WHATSAPP] Navigating to WhatsApp Web...")
        await page.goto("https://web.whatsapp.com", timeout=60000)

        print("[WHATSAPP] Waiting for login (scan QR code if needed)...")
        # Wait until the search bar or new chat button is visible
        await page.wait_for_selector('div[contenteditable="true"]', timeout=0)
        print("[WHATSAPP] Logged in successfully! Monitoring chats...")

        while True:
            try:
                # Find all unread badges
                unread_badges = await page.locator('span[aria-label*="unread message"]').all()
                current_unread_chats = []

                for badge in unread_badges:
                    try:
                        row = badge.locator('xpath=ancestor::div[@role="row"]')
                        # Extract title and preview
                        spans = await row.locator('span[title]').all()
                        if len(spans) >= 1:
                            chat_name = await spans[0].get_attribute('title')
                            msg_preview = ""
                            if len(spans) >= 2:
                                msg_preview = await spans[1].get_attribute('title')

                            current_unread_chats.append(chat_name)

                            if chat_name not in pending_replies:
                                priority = detect_priority(msg_preview)
                                delay = DELAY_MAP.get(priority, 60)
                                print(f"[WHATSAPP] New unread from {chat_name} [{priority}]: {msg_preview}")
                                pending_replies[chat_name] = {
                                    "timestamp": time.time(),
                                    "text": msg_preview,
                                    "priority": priority,
                                    "delay": delay,
                                }
                    except Exception as e:
                        pass # Ignore stale elements

                # Check timeouts based on priority-adjusted delays
                now = time.time()
                for chat_name, data in list(pending_replies.items()):
                    if chat_name not in current_unread_chats:
                        # User replied or read it manually
                        print(f"[WHATSAPP] User handled {chat_name}. Cancelling auto-reply.")
                        del pending_replies[chat_name]
                    elif now - data["timestamp"] > data["delay"]:
                        priority_label = data.get("priority", "normal")
                        print(f"[WHATSAPP] {data['delay']}s passed! Auto-replying to {chat_name} [{priority_label}]...")

                        # Generate reply with tone matching
                        reply_text = generate_reply(chat_name, data["text"])

                        # Find the chat and click it
                        chat_title_span = page.locator(f'span[title="{chat_name}"]')
                        if await chat_title_span.count() > 0:
                            row = chat_title_span.first.locator('xpath=ancestor::div[@role="row"]')
                            await row.click()
                            await asyncio.sleep(1.5)

                            # Type the message
                            input_box = page.locator('div[contenteditable="true"][data-tab="10"]')
                            if await input_box.count() > 0:
                                await input_box.fill(reply_text)
                                await asyncio.sleep(0.5)
                                await input_box.press("Enter")
                                print(f"[WHATSAPP] Sent reply to {chat_name}: {reply_text}")
                            else:
                                print(f"[WHATSAPP] Could not find input box for {chat_name}")

                        del pending_replies[chat_name]

            except Exception as e:
                print(f"[WHATSAPP] Loop error: {e}")

            await asyncio.sleep(5)


def generate_reply(sender: str, message: str) -> str:
    """Generate a context-aware, tone-matched reply."""
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Sahith is currently away. I am JARVIS, his AI assistant. I will notify him later."

    # Detect tone for the system prompt
    tone = detect_tone(message)
    priority = detect_priority(message)

    tone_instructions = {
        "casual": "Match their casual vibe. Be friendly and relaxed. Use informal language.",
        "formal": "Be polite and professional. Maintain a respectful tone.",
        "neutral": "Be natural and conversational. Not too formal, not too casual.",
    }

    priority_instructions = {
        "urgent": "This message seems urgent. Acknowledge the urgency and assure them Sahith will be notified immediately.",
        "normal": "This is a normal message. Reply naturally.",
    }

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": f"""You are JARVIS, an AI assistant managing Sahith's WhatsApp.
Sahith is currently away and hasn't replied.

TONE: {tone_instructions.get(tone, tone_instructions['neutral'])}
PRIORITY: {priority_instructions.get(priority, priority_instructions['normal'])}

Write a VERY short reply (max 1-2 sentences) on Sahith's behalf.
- Mention you are his AI assistant
- Ask what they need or how you can help
- Don't be robotic — be natural
- If the message is urgent, be more responsive and direct"""
                },
                {"role": "user", "content": f"Message from {sender}: {message}"}
            ]
        }
        r = await asyncio.to_thread(requests.post, "https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=10)
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[WHATSAPP] LLM Error: {e}")
        return "Sahith is currently away. I am JARVIS, his AI assistant. I will notify him later."

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(run_whatsapp())
