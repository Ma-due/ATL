from server.workflow.state import AgentState
import requests
import json
from typing import Dict
from server.config import FASTAPI_HOST, FASTAPI_PORT
from server.utils.logging import setup_logger

logger = setup_logger(__name__)

def fetch(state: AgentState) -> Dict:
    """CloudWatch 메시지 조회."""
    logger.info(f"fetch Start state: {state}")
    state_update = {}

    try:
        response = requests.get(f"http://{FASTAPI_HOST}:{FASTAPI_PORT}/commands")
        logger.info(f"fetch response: {response.json()}")
        response.raise_for_status()
        messages = response.json()[-1:]  # 최근 1개
        return {**messages[0], "next": "end"}
    
    except requests.RequestException as e:
        state["final_answer"] = {"response": f"조회 실패: {str(e)}"}

    state_update["final_answer"] = state["final_answer"]
    logger.info(f"fetch end state: {state}")
    return {**state_update, "next": "end"}