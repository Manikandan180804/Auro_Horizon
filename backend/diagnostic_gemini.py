import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def diagnostic():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        return

    print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}")
    genai.configure(api_key=api_key)

    print("\nAttempting to list available models...")
    try:
        models = genai.list_models()
        count = 0
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name} (Supports generateContent)")
                count += 1
        if count == 0:
            print("No models found that support generateContent.")
    except Exception as e:
        print(f"FAILED to list models: {str(e)}")

if __name__ == "__main__":
    diagnostic()
