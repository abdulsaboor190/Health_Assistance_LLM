import os
from dotenv import load_dotenv

# Import the chat model from the LangChain Google integration
from langchain_google_genai import ChatGoogleGenerativeAI

def main():
    # 1. Load the environment variables from the .env file
    load_dotenv()

    # 2. Get the API key securely from the environment
    api_key = os.getenv("GOOGLE_API_KEY")
    
    # Check if the API key is missing or still set to the placeholder
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ Error: Please setup your GOOGLE_API_KEY in the .env file.")
        print("You can get a free API key from Google AI Studio: https://aistudio.google.com/app/apikey")
        return

    print("✅ API Key loaded successfully!")

    try:
        # 3. Initialize the Gemini 2.5 Flash model
        # The ChatGoogleGenerativeAI class handles communication with Google's API
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            google_api_key=api_key
        )
        
        # 4. Generate a message
        print("\n⏳ Sending a test message to Gemini 2.5 Flash...")
        test_message = "Hello! Are you Gemini 2.5 Flash? Please reply with a short greeting."
        
        # 5. Invoke the model and print the response
        response = llm.invoke(test_message)
        
        print("\n🎯 --- Response from Gemini ---")
        print(response.content)
        print("------------------------------\n")
        print("🎉 Success! Your Python environment and Gemini integration are perfectly set up.")
        
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
