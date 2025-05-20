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
        
        content = response.choices[0].message.content.strip()
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"LLM returned non-JSON response: {content}")
            result = {"action": "path"}
            
        logger.debug(f"LLM response: {result}")

        valid_actions = ["approve", "reject", "path"]
        if result.get("action") not in valid_actions:
            logger.error(f"Invalid LLM action: {result.get('action')}, expected {valid_actions}")
            return {"next": "end"}

        if result["action"] == "path":
            logger.debug("No Y/N request found, proceeding to receive")
            return None

        state_update = {}
        if result["action"] == "approve":
            state["approved"] = True
            state["command"] = result["commands"]
            state["target"] = result["target"]
            state["intent"] = result["intent"]
            state_update = {
                "approved": state["approved"],
                "command": state["command"],
                "target": state["target"],
                "intent": state["intent"]
            }
            logger.info(f"Y input received, approved commands: {result['commands']}")
            return {**state_update, "next": "execute"}
        else:  # action == "reject"
            state["approved"] = False
            state["intent"] = "사용자의 커맨드 실행 거절"
            state_update = {
                "approved": state["approved"],
                "intent": state["intent"]
            }
            logger.info(f"N input received, commands rejected: {result['commands']}")
            return {**state_update, "next": "end"}

    except Exception as e:
        logger.error(f"LLM processing failed: {str(e)}", exc_info=True)
        state_update = {}
        return {**state_update, "next": "end"}

def receive(state: AgentState) -> Dict:
    """LLM이 bind_tools를 사용하여 Streamlit 입력의 요청 유형을 결정."""
    logger.info(f"receive Start state: {state}")
    input_type = state.get("input_type")
    raw_input = state.get("raw_input", {})
    user_input = raw_input.get("user_input", "")
    state_update = {}

    if input_type not in ["cloudwatch", "streamlit"]:
        logger.info("input type not in [cloudwatch, streamlit] return: next -> end")
        state_update["next"] = "end"
        return {**state_update, "next": "end"}

    if input_type == "cloudwatch":
        logger.info("input type == cloudwatch return: next -> generate")
        state_update["next"] = "generate"
        return {**state_update, "next": "generate"}

    # Y/N 입력 확인
    result = check_input(state)
    if result:
        return result

    client = get_llm()
    prompt = f"""
        사용자 입력의 요청 유형을 결정:
        입력: {json.dumps(raw_input, ensure_ascii=False)}
        대화 기록: {json.dumps(state["chat_history"], indent=2, ensure_ascii=False)}
        호출:
        - fetch: 클라우드워치 메시지, 알람, 모니터링 데이터 조회 (예: '클라우드워치 알람 보기').
        - generate: 리눅스 명령어, 시스템 상태 질문, 일반 대화 응답 생성 (예: 'ls -l', 'CPU 사용률 확인').
        지침:
        - 'cloudwatch', '알람', '로그', '메시지' 포함 시 'fetch' 선택.
        - EC2 인스턴스 ID (i-[0-9a-f]{{17}}) 포함 또는 CPU, 메모리, 디스크 상태 질문 시 'generate' 선택.
        반환에는 아무런 텍스트도 포함시키지 말고 Plain Text으로 반환하세요.
        반환: function_name
        예시:
        - "클라우드워치 알람 보기" → fetch
        - "ls -l" → generate
        - "i-08fb8abe21e6fa058 CPU 사용률 확인" → generate
        - "서버 메모리 상태 어때?" → generate
    """

    functions = [
        {
            "name": "fetch",
            "description": "클라우드워치 메시지, 알람, 모니터링 데이터를 조회합니다 (예: '클라우드워치 알람 보기', '로그 보기').",
            "parameters": {}
        },
        {
            "name": "generate",
            "description": "리눅스 명령어나 시스템 상태 질문에 대한 응답을 생성합니다 (예: 'ls -l', '디스크 공간 확인', 'CPU 사용률 확인', 'i-08fb8abe21e6fa058 CPU 사용률').",
            "parameters": {}
        }
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            functions=functions,
            function_call="auto"
        )
        logger.info(f"receive function call response: {response}")
        func = response.choices[0].message.content.strip()
        logger.info(f"function_call: {func}")
        state_update = {
            "input_type": "command" if func == "generate" else "query",
            "intent": func
        }
        if func == "generate":
            state["command"] = [user_input]
            state_update["command"] = state["command"]
        logger.info(f"receive end state: {state}")
        return {**state_update, "next": func}
    except Exception as e:
        logger.error(f"Function selection failed: {str(e)}", exc_info=True)
        state_update = {}
        return {**state_update, "next": "end"}