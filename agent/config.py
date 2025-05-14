from dotenv import load_dotenv
import os

load_dotenv()

# API 인증 토큰
API_TOKEN = os.getenv("API_TOKEN", "your-secret-token")
# Agent 실행 포트
AGENT_PORT = int(os.getenv("AGENT_PORT", 9917))
# EC2 인스턴스 ID
INSTANCE_ID = os.getenv("INSTANCE_ID", "i-unknown")