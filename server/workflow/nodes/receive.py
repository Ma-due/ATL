from server.workflow.state import AgentState
from server.utils.llm import get_llm
from server.utils.logging import setup_logger
import json
from typing import Dict, Optional

logger = setup_logger("receive")

def check_input(state: AgentState) -> Optional[Dict]:
    """chat_history에서 commands, target, intent를 추출하고 Y/N 입력에 따라 분기 처리."""
    logger.debug(f"Checking input: raw_input={state.get('raw_input', {})}, chat_history_len={len(state.get('chat_history', []))}")
    raw_input = state.get("raw_input", {})
    chat_history = state.get("chat_history", [])
    user_input = raw_input.get("user_input", "").strip().upper()
    client = get_llm()

    # chat_history가 비어 있으면 오류 처리
    if not chat_history:
        logger.error("No chat history available")
        return {"action": "reject", "commands": [], "target": None, "final_answer": "대화 기록이 없어 처리할 수 없습니다.", "next": "end"}

    # 가장 최근 대화 기록
    last_message = chat_history[-1]["assistant"]["content"]

    # LLM 프롬프트로 속성 추출
    prompt = f"""
        다음 마크다운 형식의 대화 기록 내용을 분석하여 요청된 속성을 추출하세요:
        
        [대화 기록 내용]
        {last_message}
        
        [지침]
        - 마크다운 문자열에서 다음 속성을 추출:
          - commands: "## 실행된 명령어" 또는 "## 추천 커맨드" 섹션의 커맨드 리스트 (예: "- `cmd`" → ["cmd"]). 없으면 빈 리스트([]).
          - target: "**명령이 실행된 인스턴스**: `...`" 또는 "**인스턴스**: `...`"의 값. "None"이면 null, 없으면 null.
          - intent: "**생성 의도** 또는 **분석**: ..."의 값. 없으면 null.
        - 출력은 반드시 순수 JSON 객체로, ```json, ```, 마크다운, 주석, 추가 텍스트를 절대 포함시키지 마세요.
        - 출력 형식:
        {{
          "commands": ["cmd1", "cmd2", ...] 또는 [],
          "target": "i-123" 또는 null,
          "intent": "의도 설명" 또는 null
        }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content.strip()
        result = json.loads(content)
        logger.debug(f"LLM response: {result}")

        # 속성 추출
        commands = result.get("commands", [])
        target = result.get("target", None)
        intent = result.get("intent", None)

        logger.info(f"추출 확인: result={result}")
        # 입력 검증
        if user_input not in ["Y", "N"]:
            return {"action": "reject", "commands": [], "target": None, "final_answer": "잘못된 입력입니다. 'Y' 또는 'N'을 입력해주세요.", "next": "end"}

        # 분기 처리
        state_update = {
            "approved": False,
            "command": commands,
            "target": target,
            "intent": intent
        }
        if user_input == "Y":
            state_update["approved"] = True
            return {**state_update, "next": "execute"}
        else:  # user_input == "N"
            state_update["final_answer"] = "사용자가 커맨드 실행을 거절하셨습니다. 추가적인 도움이 필요하신가요?"
            return {**state_update, "next": "end"}

    except Exception as e:
        logger.error(f"LLM processing failed: {str(e)}")
        return {"action": "reject", "commands": [], "target": None, "final_answer": f"처리 중 오류 발생: {str(e)}", "next": "end"}

def receive(state: AgentState) -> Dict:
    """LLM이 bind_tools를 사용하여 Streamlit 입력의 요청 유형을 결정."""
    logger.info(f"receive Start state: {state}")
    input_type = state.get("input_type")
    raw_input = state.get("raw_input", {})
    user_input = raw_input.get("user_input", "")
    user_question = state.get("user_question", False)
    state_update = {}

    if input_type not in ["cloudwatch", "streamlit"]:
        logger.info("input type not in [cloudwatch, streamlit] return: next -> end")
        state_update["next"] = "end"
        return {**state_update, "next": "end"}

    if input_type == "cloudwatch":
        logger.info("input type == cloudwatch return: next -> generate")
        state_update["next"] = "generate"
        return {**state_update, "next": "generate"}

    if user_question:
        return check_input(state)
    
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