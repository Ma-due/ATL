from typing import List

# 블랙리스트: 차단할 명령어 키워드
BLOCKED_COMMANDS: List[str] = ["rm", "reboot", "kill", "dd"]

def validate_command(command: str) -> bool:
    """
    커맨드가 블랙리스트에 포함된 키워드를 포함하지 않는지 검증
    Args:
        command: 검증할 커맨드
    Returns:
        허용 여부 (블랙리스트 키워드 미포함 시 True)
    """
    return not any(blocked in command for blocked in BLOCKED_COMMANDS)

def verify_token(token: str, expected_token: str) -> bool:
    """
    API 토큰 검증
    Args:
        token: 수신된 토큰
        expected_token: 예상 토큰
    Returns:
        유효 여부
    """
    return token == expected_token