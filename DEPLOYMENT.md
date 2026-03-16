# Aegis Health AI: Deployment Guide 🚀

This guide outlines exactly how to deploy the **Aegis Health AI** Streamlit application to a public cloud environment so it can be accessed anywhere. 

We recommend deploying to either **Streamlit Community Cloud** or **Hugging Face Spaces**. Both are free, fully support Python 3.11, and natively host Streamlit apps.

---

## ⚠️ Pre-Deployment Checklist

Before deploying, ensure your project folder (`health_assistant/`) is pushed to a **GitHub repository** and contains these exact files:

```text
health_assistant/
├── app.py                     # Main entrypoint
├── chain.py                   # RAG logic
├── ingest.py                  # Index builder
├── safety.py                  # Guardrails
├── theme.py                   # CSS/Design tokens
├── requirements.txt           # Dependencies (MUST BE EXACT)
├── .env                       # DO NOT COMMIT THIS FILE!
├── pages/
│   ├── chat_assistant.py
│   ├── symptom_checker.py
│   └── knowledge_base.py
├── data/                      # 👈 Commit at least 1 default PDF here
│   └── sample_medical_doc.pdf 
└── vectorstore/               # 👈 DO NOT commit this folder (it is generated)
```

### 1. The `.gitignore` Setup
Because `vectorstore/` contains binary database files (`index.faiss`, `index.pkl`), it is strongly advised **not** to commit it to GitHub. Furthermore, never commit your `.env` file containing your `GEMINI_API_KEY`.

Create a `.gitignore` file in your repository:
```text
.env
__pycache__/
vectorstore/
data/uploads/
```

### 2. The `requirements.txt`
I have just generated a clean, minimal `requirements.txt` for you. Ensure it is committed. It should look exactly like this:
```text
streamlit>=1.35.0
langchain>=0.2.0
langchain-google-genai>=1.0.5
langchain-huggingface>=0.0.3
faiss-cpu>=1.8.0
sentence-transformers>=3.0.0
pypdf>=4.2.0
```

---

## Option 1: Deploy to Streamlit Community Cloud (Recommended & Easiest)

Streamlit Community Cloud natively connects to your GitHub repository and automatically handles the web serving.

**Step-by-Step:**
1. **Push your code:** Push the `health_assistant` folder to a public or private GitHub repository.
2. **Log in:** Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
3. **New App:** Click the **"New app"** button.
4. **Configure the App:**
   - **Repository:** Select your GitHub repo.
   - **Branch:** `main` (or `master`).
   - **Main file path:** `app.py`
5. **Set the API Key (CRITICAL):**
   - Click **"Advanced settings"** before clicking Deploy.
   - In the **Secrets** field, paste your Gemini API key like this:
     ```toml
     GEMINI_API_KEY = "AIzaSyYourRealGeminiKeyHere............"
     ```
   - *Streamlit will automatically inject this into the environment just like your `.env` file did locally.*
6. **Deploy:** Click **Deploy!**

### Handling the Vectorstore on Streamlit Cloud
Because we `.gitignored` the `vectorstore/` folder, the app will boot up without an index.
1. Once deployed, open the app and navigate to the **Knowledge Base** page.
2. Ensure you have at least one PDF in the `data/` folder on GitHub.
3. Click the **"⚙️ Rebuild Knowledge Base"** button from inside the app.
4. It will run `ingest.py` on the cloud server, download the embedding model, and build the FAISS index. Wait for it to hit 100%.
5. The Chat and Symptom Checker pages will now work perfectly.

---

## Option 2: Deploy to Hugging Face Spaces

Hugging Face Spaces is an excellent alternative, especially for AI community projects, and offers slightly more persistent storage options.

**Step-by-Step:**
1. **Create a Space:** Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click **"Create new Space"**.
2. **Configure:**
   - **Space name:** `Aegis-Health-AI`
   - **License:** Openrail or MIT
   - **Select the Space SDK:** Choose **Streamlit**.
   - **Space hardware:** "Blank" (Free CPU Basic 16GB) is perfectly fine since FAISS runs locally on CPU and Gemini handles the heavy LLM work.
3. **Upload Files:**
   - Clone the hugging face repo to your machine OR just drag-and-drop the files from your `health_assistant` folder directly into the Hugging Face web interface.
4. **Set the API Key:**
   - Go to the **Settings** tab of your Space.
   - Scroll down to **Variables and secrets**.
   - Under **Secrets**, click **New secret**.
   - **Name:** `GEMINI_API_KEY`
   - **Value:** `AIzaSyYourRealGeminiKeyHere............`
   - Click Save.
5. **Build and Run:**
   - Hugging Face will automatically detect the `requirements.txt` and begin building the Docker image.
   - Once it says **Running**, navigate to the app. 
   - Just like with Streamlit Cloud, go to the **Knowledge Base** page and click **Rebuild Knowledge Base** to generate the FAISS index.

---

## Troubleshooting Cloud Deployments

- **Error: `ModuleNotFoundError: No module named 'langchain_google_genai'`**
  - *Fix:* Ensure `requirements.txt` is in the exact same directory as `app.py` and is spelled correctly.
- **Error: `google.api_core.exceptions.InvalidArgument: API key not valid.`**
  - *Fix:* You forgot to set the `GEMINI_API_KEY` in the Streamlit Secrets or Hugging Face Secrets menu.
- **Error: `Vector store missing. run ingest.py first`**
  - *Fix:* Navigate to the "Knowledge Base" page in your deployed app and click the "Rebuild Knowledge Base" button.
- **App falls asleep:**
  - On both free tiers of Streamlit and Hugging Face, the app will "go to sleep" if no one visits it for a few days. The next visitor will have to wait ~1 minute for it to wake up, and you **may need to click "Rebuild Knowledge Base" again** if the ephemeral storage was wiped during sleep.
