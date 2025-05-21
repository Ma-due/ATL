from server.workflow.state import AgentState
from typing import Dict

def messages(state: AgentState) -> Dict:
    return {}



"""
1. messages 만들기.
cloudwatch input 알람 메시지 만들고 저장.
receive generate execute analyze >> cloudwatch list에 저장

2. messages 조회.
cloudwatch list에서 조회
receive fetch analyze ?

3. messages 단건 조회.
"""