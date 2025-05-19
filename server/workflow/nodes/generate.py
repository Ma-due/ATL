# server/workflow/nodes/generate.py
from server.workflow.state import AgentState
from server.utils.llm import get_llm
import json
from typing import Dict

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
    입력: {json.dumps(raw_input)}
    {settings["target_instruction"]}
    반환: {{"commands": ["cmd1", ...], "target": "i-123" 또는 null, "intent": "커맨드 생성 이유 설명"}}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        result = json.loads(response.choices[0].message.content)
        state["command"] = result["commands"]
        state["target"] = result["target"]
        state["intent"] = result["intent"]

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