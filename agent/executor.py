import subprocess
from typing import Dict

def execute_command(command: str, timeout: int = 30) -> Dict[str, str | int]:
    """
    subprocess.run을 사용해 커맨드를 실행하고 결과를 반환
    Args:
        command: 실행할 커맨드 문자열
        timeout: 실행 제한 시간(초)
    Returns:
        stdout, stderr, returncode 또는 에러 메시지를 포함한 딕셔너리
    """
    try:
        result = subprocess.run(
            command,
            shell=True,  # 주의: 화이트리스트 검증 필수
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": f"'{command}' 커맨드가 {timeout}초 후 타임아웃"}
    except subprocess.SubprocessError as e:
        return {"error": f"subprocess 에러: {str(e)}"}