from dotenv import load_dotenv
import os

load_dotenv()  # .env 파일 로드

# AWS 크레덴셜
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_SQS_QUEUE_URL = os.getenv("AWS_SQS_QUEUE_URL", "")

# FastAPI 설정
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "localhost")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", 8000))
API_TOKEN = os.getenv("API_TOKEN", "your-secret-token")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")