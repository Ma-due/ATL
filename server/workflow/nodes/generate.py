# server/workflow/nodes/generate.py
from server.workflow.state import AgentState
from server.utils.llm import get_llm
import json
from typing import Dict
from server.utils.logging import setup_logger

logger = setup_logger(__name__)

def generate(state: AgentState) -> Dict:
    """입력 유형에 따라 CloudWatch 또는 Streamlit 요청을 분석하여 커맨드 리스트, 대상 인스턴스 ID, 의도 생성."""
    logger.info(f"generate Start state: {state}")
    input_type = state.get("input_type")
    raw_input = state.get("raw_input", {})
    approved = state.get("approved", False)
    client = get_llm()

    prompt_settings = {
        "cloudwatch": {
            "input_description": "CloudWatch 알람 데이터",
            "target_instruction": "대상 인스턴스 ID를 알람 데이터에서 추출"
        },
        "streamlit": {
            "input_description": "사용자 입력",
            "target_instruction": "인스턴스 ID가 명시되지 않으면 null 반환"
        }
    }

    settings = prompt_settings.get(input_type, prompt_settings["streamlit"])
    prompt = f"""
    {settings["input_description"]}을 분석하여 리눅스 커맨드 리스트, 대상 인스턴스 ID, 커맨드 의도를 생성:
    입력: {json.dumps(raw_input, ensure_ascii=False)}
    {settings["target_instruction"]}
    - 입력과 커맨드 히스토리를 기반으로 적절한 리눅스 커맨드를 생성 (예: CPU 사용량 확인 → ["top", "htop"]).
    - 커맨드 생성이 불가능하면 commands를 빈 리스트([])로 설정, intent는 문제 원인 설명.
    - 출력은 순수 JSON 문자열로, ```json, ```, 마크다운, 주석, 추가 텍스트를 절대 포함시키지 마세요.
    - JSON 형식:
    {{
      "commands": ["cmd1", ...] 또는 [],
      "target": "i-123" 또는 null,
      "intent": "커맨드 생성 이유 설명" 또는 null
    }}
    예시 입력: {{"AlarmName": "alt_cpu_high_alert", "Trigger": {{"MetricName": "CPUUtilization", "Dimensions": [{{"value": "i-123", "name": "InstanceId"}}]}}}}
    예시 출력: {{"commands": ["top", "htop"], "target": "i-123", "intent": "CPU 사용량 확인"}}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        logger.info(f"generate response: {response.choices[0].message.content}")
        result = json.loads(response.choices[0].message.content)
        logger.info(f"generate result: {result}")
        state["command"] = result["commands"]
        state["target"] = result["target"]
        state["intent"] = result["intent"]
        logger.info(f"generate Final result: {state}")
        if not state["command"] or len(state["command"]) == 0:
            state["final_answer"] = {"response": "커맨드를 생성하지 못했습니다."}
            return {"next": "end"}

        if approved:
            return {"next": "execute"}
        else:
            state["final_answer"] = {
                "response": f"커맨드: {json.dumps(state['command'])}, 의도: {state['intent']}, 실행하시겠습니까? (Y/N)"
            }
            return {"next": "end"}
    except Exception as e:
        state["final_answer"] = {"response": f"커맨드 생성 실패: {str(e)}"}
        return {"next": "end"}