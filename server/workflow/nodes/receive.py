# server/workflow/nodes/receive.py
from server.workflow.state import AgentState
from server.utils.llm import get_llm
import json
from typing import Dict, Optional
from datetime import datetime

def check_input(state: AgentState) -> Optional[Dict]:
    """chat_history와 raw_input을 통해 Y/N 승인 요청 여부 판단 및 처리."""
    raw_input = state.get("raw_input", {})
    text = raw_input.get("text", "").lower()
    chat_history = state.get("chat_history", [])
    client = get_llm()

    prompt = f"""
    다음 대화 기록을 분석하여 사용자가 커맨드 실행을 승인해야 하는 Y/N 요청이 있는지 확인:
    대화 기록: {json.dumps(chat_history[-5:])}
    입력: {json.dumps(raw_input)}
    - Y/N 요청이 있으면, 입력이 Y/N인지 판단.
    - Y: 승인, N: 거부.
    - 요청 없으면 none 반환.
    - Y/N 요청 시, 관련 커맨드와 의도 복원.
    반환: {{"action": "approve" | "reject" | "none", "commands": ["cmd1", ...], "intent": "의도 설명", "target": "i-123" 또는 null}}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        result = json.loads(response.choices[0].message.content)

        if result["action"] == "none":
            return None

        # Y/N 요청이 있는 경우
        if text not in ["y", "n"]:
            state["final_answer"] = {"response": "Y 또는 N을 입력해주세요"}
            return {"next": "end"}

        # chat_history 업데이트
        state["chat_history"] = state.get("chat_history", []) + [{
            "role": "user",
            "content": text,
            "timestamp": datetime.utcnow().isoformat()
        }]

        if result["action"] == "approve":
            state["approved"] = True
            state["command"] = result["commands"]
            state["target"] = result["target"]
            state["intent"] = result["intent"]
            return {"next": "execute"}
        else:  # action == "reject"
            state["approved"] = False
            state["final_answer"] = {"response": f"커맨드 실행 취소: {json.dumps(result['commands'])}, 의도: {result['intent']}"}
            return {"next": "end"}

    except Exception as e:
        state["final_answer"] = {"response": f"입력 처리 실패: {str(e)}"}
        return {"next": "end"}

def receive(state: AgentState) -> Dict:
    """LLM이 bind_tools를 사용하여 Streamlit 입력의 요청 유형을 결정."""
    input_type = state.get("input_type")
    raw_input = state.get("raw_input", {})

    if input_type not in ["cloudwatch", "streamlit"]:
        return {"next": "end"}

    if input_type == "cloudwatch":
        return {"next": "generate"}

    # Y/N 입력 확인
    result = check_input(state)
    if result:
        return result

    client = get_llm()
    prompt = f"""
    사용자 입력의 요청 유형을 결정:
    입력: {json.dumps(raw_input)}
    호출:
    - fetch: cloudwatch_messages 조회.
    - generate: 커맨드/대화 생성.
    """

    functions = [
        {
            "name": "fetch",
            "description": "사용자의 요청에 따라 최근 cloudwatch_messages 실행 내역을 조회합니다.",
            "parameters": {}
        },
        {
            "name": "generate",
            "description": "사용자의 요청에 따라 리눅스 커맨드 또는 대화 응답을 생성합니다.",
            "parameters": {}
        }
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            functions=functions,
            function_call="auto"
        )
        func = response.choices[0].message.function_call
        return {"next": "fetch" if func and func.name == "fetch" else "generate"}
    except Exception:
        return {"next": "end"}