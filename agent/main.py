from fastapi import FastAPI, HTTPException, Header
from .executor import execute_command
from .security import validate_command, verify_token
from .config import API_TOKEN, AGENT_PORT
import uvicorn
from .models.models import ExecuteRequest, ExecuteResponse
from typing import List


app = FastAPI()


@app.post("/execute", response_model=List[ExecuteResponse])
def execute_command_endpoint(request: ExecuteRequest, 
                             authorization: str = Header(default="")) -> List[ExecuteResponse]:
    """
    서버로부터 커맨드를 수신하고 실행
    Args:
        request: 커맨드와 instance_id 포함
        authorization: API 토큰 헤더
    Returns:
        실행 결과
    """
    print(f"agent.main.execute_command_endpoint input: {request}")
    # 토큰 검증
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else ""
    if not verify_token(token, API_TOKEN):
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰")
    
    # 커맨드 검증
    if not validate_command(request.command):
        raise HTTPException(status_code=403, detail="허용되지 않은 커맨드")
    
    # 커맨드 실행
    result = execute_command(request.command)
    # ExecuteResponse로 반환
    print(f"agent.main.execute_command_endpoint output: {result}")
    return result

if __name__ == "__main__":
    # Agent 서버 실행
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)