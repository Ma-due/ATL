from typing import Dict
from server.workflow.state import AgentState
from server.utils.llm import get_llm
from server.utils.logging import setup_logger
import json
import re

logger = setup_logger(__name__)

def analyze(state: AgentState) -> Dict:
    """실행 결과를 포맷팅하고 시스템 상태를 분석하여 요약."""
    logger.info(f"analyze Start state: {state}")
    
    # 상태에서 필요한 데이터 추출
    execution_result = state.get("execution_result", [])
    target = state.get("target")
    input_type = state.get("input_type")
    intent = state.get("intent")
    approved = state.get("approved")
    
    # 디버깅: execution_result 구조 확인
    logger.debug(f"execution_result: {execution_result}")

    # 실행 결과가 없는 경우
    if not execution_result:
        state["final_answer"] = "분석할 실행 결과가 없음"
        logger.info(f"analyze end state: {state}")
        return state

    # 명령어 추출
    commands = state.get("command", [])
    logger.debug(f"Extracted commands: {commands}")

    # LLM 호출로 단일 응답 생성
    client = get_llm()
    prompt = f"""
    다음 정보를 기반으로 실행 결과를 포맷팅하고 시스템 상태를 요약하여 단일 응답으로 제공하세요:
    - 커맨드: {json.dumps(commands, ensure_ascii=False)}
    - 실행 결과: {json.dumps(execution_result, ensure_ascii=False)}
    - 의도: {intent}
    - 대상 인스턴스: {target}
    - 입력 유형: {input_type}
    - 지침:
      - 실행 결과와 시스템 상태를 하나의 깔끔한 문자열로 통합.
      - 형식 예시:
        실행 결과:
        명령어: ps aux --sort=-%cpu | head -n 10
        상태: 성공
        출력: USER PID %CPU...
        명령어: sar 1 5
        상태: 성공
        출력: Linux 6.1...
        시스템 상태: CPU 사용량 0.19%, 디스크 정상, 문제 없음.
      - **반드시 유효한 JSON 형식으로만 반환** (예: {{"response": "통합된 응답"}}).
      - Markdown (예: ```json), 코드 블록, 추가 텍스트 절대 포함 금지.
    반환: {{"response": "통합된 응답"}}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        logger.debug(f"LLM raw response: {content}")
        
        # Markdown 코드 블록 제거 (안전장치)
        content = re.sub(r'```json\n|\n```', '', content).strip()
        result = json.loads(content)
        
        # final_answer를 문자열로 설정
        state["final_answer"] = result["response"]
        logger.info(f"-----------------------------------------------------------")
        logger.info(f"analyze end state: {state['final_answer']}")
        logger.info(f"-----------------------------------------------------------")

        if not approved:
            state["final_answer"] += "\n커맨드를 실행하시겠습니까? (Y/N)"

        return state
    
    except Exception as e:
        logger.error(f"analyze failed: {str(e)}")
        state["final_answer"] = f"분석 실패: {str(e)}"
        logger.info(f"analyze end state: {state}")
        return state