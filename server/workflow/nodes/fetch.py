# server/workflow/nodes/fetch.py
from server.workflow.state import AgentState
import requests
import json
from typing import Dict
from server.config import FASTAPI_HOST, FASTAPI_PORT
from server.utils.logging import setup_logger

logger = setup_logger(__name__)

def fetch(state: AgentState) -> Dict:
    try:
        response = requests.get(f"http://{FASTAPI_HOST}:{FASTAPI_PORT}/commands")
        logger.info(f"fetch response: {response.json()}")
        response.raise_for_status()
        messages = response.json()[-5:]  # 최근 5개
        state["final_answer"] = {"response": f"cloudwatch_messages: {json.dumps(messages)}"}
    except requests.RequestException as e:
        state["final_answer"] = {"response": f"조회 실패: {str(e)}"}
    return {"next": "end"}