from pydantic import BaseModel
from typing import Optional, Dict, List

class Alarm(BaseModel):
    raw_data: dict  # 원본 JSON 데이터

class ExecuteRequest(BaseModel):
    command: Optional[List[str]]    # 실행할 커맨드
    agent: Optional[str] # 대상 인스턴스 ID, 기본값 환경 변수

class ExecuteResponse(BaseModel):
    output: Optional[str]
    error: Optional[str]
    status: str
