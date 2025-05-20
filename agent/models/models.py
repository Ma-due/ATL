from pydantic import BaseModel
from typing import Optional, List


class ExecuteRequest(BaseModel):
    command: Optional[List[str]]    # 실행할 커맨드
    agent: Optional[str] # 대상 인스턴스 ID, 기본값 환경 변수

class ExecuteResponse(BaseModel):
    command: str  # 실행된 명령어 (문자열)
    stdout: Optional[str]  # 표준 출력
    stderr: Optional[str]  # 표준 에러
    returncode: int  # 종료 코드