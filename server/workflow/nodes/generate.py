from server.workflow.state import AgentState
from server.utils.llm import get_llm
import json
from typing import Dict
from server.utils.logging import setup_logger

logger = setup_logger(__name__)

def generate(state: AgentState) -> Dict:
    """입력 유형에 따라 CloudWatch 또는 Streamlit 요청을 분석하여 커맨드 리스트, 대상 인스턴스 ID, 의도 생성."""
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
    - 입력과 커맨드 히스토리를 기반으로 적절한 리눅스 커맨드를 생성 (예: CPU 사용량 확인 → ["ps aux --sort=-%cpu | head -n 10", "sar 1 5"]).
    - 커맨드 생성이 불가능하면 commands를 빈 리스트([])로 설정, intent는 커맨드를 생성한 이유 설명.
    - 출력은 순수 JSON 문자열로, ```json, ```, 마크다운, 주석, 추가 텍스트를 절대 포함시키지 마세요.
    - JSON 형식:
    {{
      "commands": ["cmd1", ...] 또는 [],
      "target": "i-123" 또는 null,
      "intent": "커맨드 생성 이유 설명" 또는 null
    }}
    예시 입력: {{"AlarmName": "alt_cpu_high_alert", "Trigger": {{"MetricName": "CPUUtilization", "Dimensions": [{{"value": "i-123", "name": "InstanceId"}}]}}}}
    예시 출력: {{"commands": ["ps aux --sort=-%cpu | head -n 10", "sar 1 5"], "target": "i-123", "intent": "높은 CPU 사용률은 애플리케이션 부하, 프로세스 문제, 또는 외부 테스트로 인한 것일 수 있음."}}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        logger.info(f"generate response: {response.choices[0].message.content}")
        result = json.loads(response.choices[0].message.content)

        state["command"] = result["commands"]
        state["target"] = result["target"]
        state["intent"] = result["intent"]
        logger.info(f"generate Final result: {state}")

        # 상태 업데이트 반환
        state_update = {
            "command": state["command"],
            "target": state["target"],
            "intent": state["intent"]
        }

        if not state["command"] or len(state["command"]) == 0:
            state["final_answer"] = "커맨드를 생성할 수 없습니다."
            state["chat_history"] = state.get("chat_history", []) + [{
                "user": {"content": raw_input.get("user_input", "")},
                "assistant": {"content": state["final_answer"]}
            }]
            state_update["final_answer"] = state["final_answer"]
            state_update["chat_history"] = state["chat_history"]
            logger.info(f"generate end state: {state}")
            return {**state_update, "next": "end"}

        if approved:
            return {**state_update, "next": "execute"}
        else:
            state["final_answer"] = "사용자가 실행을 거부하셨습니다. 추가적인 도움이 필요하신가요?"
            state["chat_history"] = state.get("chat_history", []) + [{
                "user": {"content": raw_input.get("user_input", "")},
                "assistant": {"content": state["final_answer"]}
            }]
            state_update["final_answer"] = state["final_answer"]
            state_update["chat_history"] = state["chat_history"]
            logger.info(f"generate end state: {state}")
            return {**state_update, "next": "end"}
    except Exception as e:
        state["final_answer"] = f"커맨드 생성 실패: {str(e)}"
        state["chat_history"] = state.get("chat_history", []) + [{
            "user": {"content": raw_input.get("user_input", "")},
            "assistant": {"content": state["final_answer"]}
        }]
        state_update = {
            "final_answer": state["final_answer"],
            "chat_history": state["chat_history"]
        }
        logger.error(f"generate failed: {str(e)}")
        return {**state_update, "next": "end"}