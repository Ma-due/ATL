# server/utils/llm.py
from openai import OpenAI
from server.config import OPENAI_API_KEY

def get_llm() -> OpenAI:
    """OpenAI LLM 클라이언트를 반환."""
    api_key = OPENAI_API_KEY

    if not api_key:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. 환경 변수를 확인하세요.")

    try:
        client = OpenAI(
            api_key=api_key,
            timeout=30.0  # 요청 타임아웃 30초
        )
        return client
    except Exception as e:
        raise RuntimeError(f"OpenAI 클라이언트 초기화 실패: {str(e)}")