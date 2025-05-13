from typing import List

ALLOWED_COMMANDS: List[str] = ["top", "df -h", "ps aux", "free -m"]

def validate_command(command: str) -> bool:
    """
    커맨드가 화이트리스트에 포함되는지 검증
    Args:
        command: 검증할 커맨드
    Returns:
        허용 여부
    """
    return any(allowed in command for allowed in ALLOWED_COMMANDS)

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