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

    # 명령어 추출
    commands = state.get("command", [])
    logger.debug(f"Extracted commands: {commands}")

    # LLM 호출로 단일 응답 생성
    client = get_llm()
    prompt = f"""
    다음 정보를 기반으로 지침을 참고해서 반환을 마크다운 형식으로 제공하세요:
    
    [정보]
    - 커맨드: {json.dumps(commands, ensure_ascii=False)}
    - 실행 결과: {json.dumps(execution_result, ensure_ascii=False)}
    - 의도: {intent}
    - 대상 인스턴스: {target}
    - 입력 유형: {input_type}
    - 사용자 승인: {approved}
    
    [지침]
    - 시스템 상태를 간결한 마크다운 문자열로 요약 (CPU 사용량, 디스크 상태, 문제 여부 포함).
    - 모든 명령어와 실행 결과를 포함, 가변적 개수에 맞게 동적으로 처리.
    - 실행 결과의 각 명령어는 `### \`커맨드\`` 형식으로 표시 (예: ### `ps aux --sort=-%cpu | head -n 10`).
    - 실행 결과는 코드 블록(```text)으로, 상태(성공/실패) 명시, 전체 stdout 포함.
    - 보고서 상단에 "명령이 실행된 인스턴스: `{target}`" 추가.
    - 요약은 시스템 상태와 데이터 기반 분석(예: CPU 피크 원인, 프로세스 이상 여부)을 포함.
    - 마크다운 형식을 자유롭게 선택하되, Streamlit 렌더링에 적합하게 가독성 유지 (헤딩, 리스트, 코드 블록 활용).
    - **반드시 유효한 JSON 형식으로만 반환** (예: {{"answer": "반환 예시"}}).
    - Markdown (예: ```json), 코드 블록, 추가 텍스트 절대 포함 금지.
    
    [반환 예시] 
    # 시스템 상태 보고서
    
    **명령이 실행된 인스턴스**: `i-08fb8abe21e6fa058`
    ## 실행된 명령어
    - `ps aux --sort=-%cpu | head -n 10`
    - `sar 1 5`

    **생성 의도**: 높은 CPU 사용률은 애플리케이션 부하, 프로세스 문제, 또는 외부 테스트로 인한 것일 수 있음."
    
    ## 명령어 실행 결과
    ### `ps aux --sort=-%cpu | head -n 10`
    **상태**: 성공
    ```text
    USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND
    ec2-user 314273 0.1 2.2 347424 44988 ? Ssl 01:31 0:19 /usr/bin/python3.12 -m uvicorn...
    ...
    ```

    ### `sar 1 5`
    **상태**: 성공
    ```text
    Linux 6.1.134-150.224.amzn2023.x86_64...
    Average: all 0.79 0.00 1.39 0.00 1.39 96.44
    ```
    ## 시스템 상태 요약
    - **CPU 사용량**: 평균 0.79%, 최대 7% (05:14:34 순간 피크)
    - **디스크 상태**: 정상
    - **문제 여부**: 없음
    
    **분석**: 높은 CPU 사용률 알람(94.1%) 발생, 그러나 현재 데이터로는 정상. 순간 부하(7% system) 확인, 지속성 없음. 추가 모니터링 권장.
    **인스턴스**: i-08fb8abe21e6fa058 
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        logger.debug(f"LLM raw response: {content}")
        
        result = json.loads(content)
        # final_answer를 문자열로 설정
        state["final_answer"] = result["answer"]

        if not approved:
            state["final_answer"] += "\\n커맨드를 실행하시겠습니까? (Y/N)"

        return state
    
    except Exception as e:
        logger.error(f"analyze failed: {str(e)}")
        state["final_answer"] = f"분석 실패: {str(e)}"
        logger.info(f"analyze end state: {state}")
        return state