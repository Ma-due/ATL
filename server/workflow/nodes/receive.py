# server/workflow/nodes/receive.py
from server.workflow.state import AgentState
from server.utils.llm import get_llm
from server.utils.logging import setup_logger
import json
from typing import Dict, Optional
from datetime import datetime

logger = setup_logger("receive")

def check_input(state: AgentState) -> Optional[Dict]:
    """chat_history와 raw_input을 통해 Y/N 승인 요청 여부 판단 및 처리."""
    logger.debug(f"Checking input: raw_input={state.get('raw_input', {})}, chat_history_len={len(state.get('chat_history', []))}")
    raw_input = state.get("raw_input", {})
    chat_history = state.get("chat_history", [])
    client = get_llm()

    prompt = f"""
    다음 대화 기록과 입력을 분석하여 사용자가 커맨드 실행을 승인해야 하는 Y/N 요청이 있는지 확인:
    대화 기록: {json.dumps(chat_history[-5:], ensure_ascii=False)}
    입력: {json.dumps(raw_input, ensure_ascii=False)}
    - 대화 기록에 "실행하시겠습니까? (Y/N)" 또는 유사한 문구가 포함된 경우:
      - 입력이 "Y"이면 action을 "approve"로 설정.
      - 입력이 "N"이면 action을 "reject"로 설정.
      - 관련 커맨드, 의도, 타겟을 대화 기록에서 복원.
    - Y/N 요청이 없으면 action을 "path"로 설정, commands, intent, target은 빈 값([] 또는 null) 반환.
    - 출력은 반드시 아래 JSON 형식을 엄격히 준수:
    {{
      "action": "approve" | "reject" | "path",
      "commands": ["cmd1", ...] 또는 [],
      "intent": "의도 설명" 또는 null,
      "target": "i-123" 또는 null
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        result = json.loads(response.choices[0].message.content)
        logger.debug(f"LLM response: {result}")

        # 응답 검증
        valid_actions = ["approve", "reject", "path"]
        if result.get("action") not in valid_actions:
            logger.error(f"Invalid LLM action: {result.get('action')}, expected {valid_actions}")
            return {"next": "end"}

        if result["action"] == "path":
            logger.debug("No Y/N request found, proceeding to receive")
            return None

        if result["action"] == "approve":
            state["approved"] = True
            state["command"] = result["commands"]
            state["target"] = result["target"]
            state["intent"] = result["intent"]
            logger.info(f"Y input received, approved commands: {result['commands']}")
            return {"next": "execute"}
        else:  # action == "reject"
            state["approved"] = False
            state["intent"] = "사용자의 커맨드 실행 거절"
            logger.info(f"N input received, commands rejected: {result['commands']}")
            return {"next": "end"}

    except Exception as e:
        logger.error(f"LLM processing failed: {str(e)}", exc_info=True)
        return {"next": "end"}

def receive(state: AgentState) -> Dict:
    """LLM이 bind_tools를 사용하여 Streamlit 입력의 요청 유형을 결정."""
    logger.info(f"Receive state: {state}")
    input_type = state.get("input_type")
    raw_input = state.get("raw_input", {})

    if input_type not in ["cloudwatch", "streamlit"]:
        logger.info("input type not in [cloudwatch, streamlit] return: next -> end")
        return {"next": "end"}

    if input_type == "cloudwatch":
        logger.info("input type == cloudwatch return: next -> generate")
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
            "description": "사용자의 요청에 따라 최근 cloudwatch_messages 내역을 조회합니다.",
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
        logger.info(f"function_call: {func}")
        return {"next": "fetch" if func and func.name == "fetch" else "generate"}
    except Exception:
        logger.info("function_call error return: next -> end")
        return {"next": "end"}