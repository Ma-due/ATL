from dotenv import load_dotenv
import os

load_dotenv()

# FastAPI 설정
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "localhost")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", 8000))
API_TOKEN = os.getenv("API_TOKEN", "your-secret-token")

# Streamlit 설정
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", 8501))