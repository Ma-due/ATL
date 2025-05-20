from server.workflow.state import AgentState
from server.utils.llm import get_llm
import json
from typing import Dict
from server.utils.logging import setup_logger

logger = setup_logger(__name__)

def analyze(state: AgentState) -> Dict:
    """실행 결과를 예쁘게 포맷팅하고 시스템 상태를 분석하여 요약."""
    logger.info(f"analyze Start state: {state}")
    execution_result = state.get("execution_result")
    commands = execution_result.get("commands", []) if execution_result else []
    results = execution_result.get("results", []) if execution_result else []
    target = state.get("target")
    input_type = state.get("input_type")
    intent = state.get("intent")
    approved = state.get("approved")

    # 상태 업데이트 딕셔너리
    state_update = {}

    if not execution_result or not results:
        state["final_answer"] = {"response": "분석할 실행 결과가 없음"}
        state_update["final_answer"] = state["final_answer"]
        logger.info(f"analyze end state: {state}")
        return {**state_update, "next": "end"}

    client = get_llm()
    prompt = f"""
    다음 정보를 기반으로 실행 결과를 예쁘게 포맷팅하고 시스템 상태를 요약하세요.
    만약 approved 값이 False이면, 실행에 대한 여부를 승인받으세요:

    커맨드: {json.dumps(commands)}
    의도: {intent}
    실행 결과: {json.dumps(execution_result)}
    대상 인스턴스: {target}
    입력 유형: {input_type}
    사용자 승인: {approved}
    - 결과를 읽기 쉽게 정리 (예: 커맨드별 출력, 성공/실패 상태, 의도 포함).
    - 시스템 상태 요약 (예: CPU 사용량, 디스크 상태, 문제 여부).
    - approved가 False이면 summary 마지막 줄에 "실행하시겠습니까? (Y/N)" 포함.
    반환: {{"formatted_output": "정리된 결과", "summary": "상태 요약"}}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        result = json.loads(response.choices[0].message.content)
        state["final_answer"] = {
            "response": f"{result['formatted_output']}\n\n요약: {result['summary']}"
        }
        state_update["final_answer"] = state["final_answer"]
        logger.info(f"analyze end state: {state}")
        return {**state_update, "next": "end"}
    except Exception as e:
        state["final_answer"] = {"response": f"분석 실패: {str(e)}"}
        state_update["final_answer"] = state["final_answer"]
        logger.error(f"analyze failed: {str(e)}")
        logger.info(f"analyze end state: {state}")
        return {**state_update, "next": "end"}