# server/workflow/state.py
from typing import TypedDict, List, Optional, Dict

class AgentState(TypedDict):
    input_type: str # 입력 유형: 'streamlit' 또는 'cloudwatch'
    raw_input: Dict # 원본 입력: Streamlit 텍스트 또는 CloudWatch 알람 JSON
    command: Optional[List[str]] # 생성된 리눅스 커맨드
    target: Optional[str] # 대상 인스턴스 ID
    approved: Optional[bool] # 사용자 승인 여부: True, False, None
    execution_result: Optional[Dict] # 커맨드 실행 결과
    final_answer: Optional[Dict] # 최종 User 리턴 메시지
    chat_history: List[Dict] # 현재 워크플로우의 채팅 히스토리
    intent: Optional[str] # 커맨드 생성 의도
    user_question: Optional[str] # 사용자 질문