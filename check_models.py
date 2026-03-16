import os
import google.generativeai as genai
from dotenv import load_dotenv

def main():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ Error: API Key is missing or invalid in .env file.")
        return

    genai.configure(api_key=api_key)
    
    print("🔍 Fetching available models for your API key...")
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        print("\n✅ Successfully retrieved available models:")
        for model in models:
            print(f"- {model}")
            
        print("\n💡 TIP: Look for names like 'models/gemini-1.5-flash' or 'models/gemini-pro'")
        print("Update your test.py script to match exactly one of these model names (remove the 'models/' prefix if Langchain adds it automatically).")
        
    except Exception as e:
        print(f"\n❌ Failed to fetch models: {e}")

if __name__ == "__main__":
    main()
