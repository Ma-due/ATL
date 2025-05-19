# server/workflow/nodes/execute.py
from server.workflow.state import AgentState
from server.utils.server_info import get_agent_url
from server.config import FASTAPI_HOST, FASTAPI_PORT
import requests
from typing import Dict


def execute(state: AgentState) -> Dict:
    """command 리스트와 target을 사용하여 /execute API 호출."""
    commands = state.get("command", [])
    target = state.get("target")

    if not commands:
        state["final_answer"] = {"response": "실행할 커맨드가 없음"}
        return {"next": "end"}

    try:
        agent_url = get_agent_url(target)
        payload = {"command": commands, "agent": agent_url}
        response = requests.post(f"{FASTAPI_HOST}:{FASTAPI_PORT}/execute", json=payload)
        response.raise_for_status()
        state["execution_result"] = {"results": response.json}
        return {"next": "analyze"}
    except requests.RequestException as e:
        state["final_answer"] = {"response": f"실행 실패: {str(e)}"}
        return {"next": "end"}