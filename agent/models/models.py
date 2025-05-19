from pydantic import BaseModel
from typing import Optional, Dict

class ExecuteRequest(BaseModel):
    command: Optional[str]    # 실행할 커맨드
    instance_id: Optional[str] # 대상 인스턴스 ID, 기본값 환경 변수

class ExecuteResponse(BaseModel):
    output: Optional[str]
    error: Optional[str]
    status: str
