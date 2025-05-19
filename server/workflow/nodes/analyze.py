# server/workflow/nodes/analyze.py
from server.workflow.state import AgentState
from server.utils.llm import get_llm
import json
from typing import Dict

def analyze(state: AgentState) -> Dict:
    """실행 결과를 예쁘게 포맷팅하고 시스템 상태를 분석하여 요약."""
    execution_result = state.get("execution_result")
    commands = execution_result.get("commands", []) if execution_result else []
    results = execution_result.get("results", []) if execution_result else []
    target = state.get("target")
    input_type = state.get("input_type")
    intent = state.get("intent")

    if not execution_result or not results:
        state["final_answer"] = {"response": "분석할 실행 결과가 없음"}
        return {"next": "end"}

    client = get_llm()
    prompt = f"""
    다음 정보를 기반으로 실행 결과를 예쁘게 포맷팅하고 시스템 상태를 요약:
    커맨드: {json.dumps(commands)}
    의도: {intent if intent else '지정되지 않음'}
    실행 결과: {json.dumps(results)}
    대상 인스턴스: {target if target else '지정되지 않음'}
    입력 유형: {input_type}
    - 결과를 읽기 쉽게 정리 (예: 커맨드별 출력, 성공/실패 상태, 의도 포함).
    - 시스템 상태 요약 (예: CPU 사용량, 디스크 상태, 문제 여부).
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
        return {"next": "end"}
    except Exception as e:
        state["final_answer"] = {"response": f"분석 실패: {str(e)}"}
        return {"next": "end"}