from typing import Dict, List, Any
import requests
from pydantic import ValidationError
from server.models.models import ExecuteResponse
from server.config import FASTAPI_HOST, FASTAPI_PORT
from server.utils.logging import setup_logger
from server.utils.server_info import get_agent_url

logger = setup_logger(__name__)

AgentState = Dict[str, Any]

def execute(state: AgentState) -> Dict:
    """
    command 리스트와 target을 사용하여 /execute API 호출.
    
    Args:
        state: 에이전트 상태 (command와 target 포함)
    Returns:
        다음 노드와 업데이트된 상태
    """
    commands = state.get("command", [])
    target = state.get("target")

    if not commands:
        logger.warning("No command provided in state")
        state["execution_result"] = [
            {
                "command": "",
                "stdout": None,
                "stderr": "실행할 커맨드가 없음",
                "returncode": 1
            }
        ]
        return {"next": "finish"}

    try:
        agent_url = get_agent_url(target)
        # payload를 딕셔너리로 생성
        payload = {"command": commands, "agent": target, "url": agent_url}
        logger.info(f"Sending request to {FASTAPI_HOST}:{FASTAPI_PORT}/execute with payload: {payload}")
        
        response = requests.post(
            f"http://{FASTAPI_HOST}:{FASTAPI_PORT}/execute",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()

        # 응답을 List[ExecuteResponse]로 변환
        results = response.json()
        if not isinstance(results, list):
            logger.error(f"Expected list response, got: {type(results)}, data: {results}")
            state["execution_result"] = [
                {"command": cmd, "stdout": None, "stderr": "Invalid response format from server", "returncode": 1}
                for cmd in commands
            ]
            return {"next": "finish"}

        # ExecuteResponse를 역직렬화해 execution_result에 저장
        state["execution_result"] = [
            {
                "command": result.get("command", cmd),
                "stdout": result.get("stdout"),
                "stderr": result.get("stderr"),
                "returncode": result.get("returncode", 1)
            }
            for cmd, result in zip(commands, results)
            if isinstance(result, dict)
        ]

        if not state["execution_result"]:
            logger.error(f"No valid ExecuteResponse objects in response: {results}")
            state["execution_result"] = [
                {"command": cmd, "stdout": None, "stderr": "No valid response data", "returncode": 1}
                for cmd in commands
            ]
            return {"next": "finish"}

        logger.info(f"Execution successful, commands: {commands}")
        return {"next": "analyze"}

    except requests.RequestException as e:
        logger.error(f"Agent request failed: {str(e)}")
        state["execution_result"] = [
            {"command": cmd, "stdout": None, "stderr": f"Agent execution failed: {str(e)}", "returncode": 1}
            for cmd in commands
        ]
        return {"next": "finish"}
    except ValidationError as e:
        logger.error(f"Response validation failed: {str(e)}, data: {results}")
        state["execution_result"] = [
            {"command": cmd, "stdout": None, "stderr": f"Response validation failed: {str(e)}", "returncode": 1}
            for cmd in commands
        ]
        return {"next": "finish"}