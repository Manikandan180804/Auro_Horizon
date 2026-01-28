import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Expanded model pool for maximum resilience
MODELS_TO_TRY = [
    'gemini-2.5-flash', 
    'gemini-2.5-flash-lite', 
    'gemini-3-flash-preview',
    'gemini-1.5-flash', 
    'gemini-1.5-pro',
    'gemini-flash-lite-latest'
]

# Varied local mock responses for "High Demand" mode
AURA_LOCAL_RESPONSES = [
    "I've noted your interest! My deep-thinking processor is catching its breath, but I've updated your Intelligence Stream with some fresh insights. What else is on your mind?",
    "That's a fascinating perspective. I'm currently running in light-mode due to high demand, but I've captured those new interests for you. Take a look at your curated stream!",
    "I'm keeping track of everything you're telling me! While I can't provide a deep analysis right this second, I've adjusted your personalized suggestions to reflect our conversation.",
    "Aura is here! I'm processing a a lot of requests right now, so I'll keep this brief: Interests updated, and your Intelligence Stream is ready for exploration.",
    "I love where this conversation is going. My secondary systems have updated your profile based on that. I'll be back to full power shortly!"
]

# Simple in-memory cache
AI_CACHE = {}

async def get_ai_response(prompt: str):
    if not GEMINI_API_KEY:
        return "Gemini API Key not found. Please set it in the .env file."
    
    if prompt in AI_CACHE:
        return AI_CACHE[prompt]
        
    last_error = ""
    quota_exceeded = False
    
    for model_name in MODELS_TO_TRY:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            AI_CACHE[prompt] = response.text
            return response.text
        except Exception as e:
            last_error = str(e)
            if "429" in last_error or "quota" in last_error.lower():
                quota_exceeded = True
                continue # Try next model
            if "404" in last_error:
                continue
            return f"Error communicating with AI: {last_error}"
    
    if quota_exceeded:
        return f"QUOTA_EXCEEDED: All models throttled."
        
    return f"Failed to connect to any Gemini models. Last error: {last_error}"

async def analyze_interests(message: str, current_interests: str = ""):
    prompt = f"""
    The user said: "{message}"
    Their current known interests are: {current_interests}
    
    Identify any new specific interests (tech, design, food, science, lifestyle, etc.) from the user's message.
    Return ONLY a comma-separated list of keywords. Do not include any other text.
    Keywords:
    """
    response = await get_ai_response(prompt)
    if "Failed to connect" in response or "QUOTA_EXCEEDED" in response:
        return current_interests
    
    # Clean up response to ensure only keywords are taken
    clean_interests = response.replace("Keywords:", "").strip().lower()
    return clean_interests

async def get_chat_and_interests(message: str, current_interests: str = ""):
    """
    Combines chat reply and interest analysis into a single Gemini call to save quota.
    """
    prompt = f"""
    You are Aura, a personalized AI assistant.
    The user says: "{message}"
    Their current known interests are: {current_interests}
    
    Tasks:
    1. Respond to the user's message warmly and professionally.
    2. Identify any new specific interests (tech, design, food, etc.) from this message.
    
    Return ONLY a JSON object with two keys:
    "reply": Your message to the user.
    "interests": A comma-separated list of ALL current and new specific interests.
    
    Format:
    {{
      "reply": "...",
      "interests": "..."
    }}
    """
    response = await get_ai_response(prompt)
    
    if "QUOTA_EXCEEDED" in response:
        import random
        return {
            "reply": random.choice(AURA_LOCAL_RESPONSES),
            "interests": current_interests # Could also try a simpler local parser here
        }
        
    try:
        import json
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return {
                "reply": data.get("reply", ""),
                "interests": data.get("interests", current_interests)
            }
    except Exception as e:
        print(f"Error parsing combined AI response: {e}")
        
    return {
        "reply": response,
        "interests": current_interests
    }

async def score_recommendations(interests: list[str], items: list[dict]):
    """
    Use Gemini to score recommendations based on user interests.
    Returns a list of (score, item) tuples.
    """
    if not items:
        return []
        
    items_text = "\n".join([f"- ID {i} | {item['title']} | {item['category']} | {item['description']}" for i, item in enumerate(items)])
    
    prompt = f"""
    User Interests: {", ".join(interests)}
    
    Available Suggestions:
    {items_text}
    
    Evaluate how well each suggestion matches the user's interests.
    Score each item from 0 to 10 (10 being perfect match).
    Return ONLY a JSON list of objects with "id" (the ID provided above) and "score" keys.
    Format: [{{"id": 0, "score": 8}}, ...]
    """
    
    response = await get_ai_response(prompt)
    if "QUOTA_EXCEEDED" in response:
        print("API Quota exceeded. Using default random selection.")
        return [(0, item) for item in items]
        
    try:
        # Simple extraction if response contains other text
        import json
        import re
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            scores = json.loads(json_match.group())
            # Map scores back to items
            scored_items = []
            for score_data in scores:
                idx = score_data.get("id")
                score = score_data.get("score", 0)
                if idx is not None and 0 <= idx < len(items):
                    scored_items.append((score, items[idx]))
            return scored_items
    except Exception as e:
        print(f"Error parsing Gemini scoring: {e}")
    
    return [(0, item) for item in items]
