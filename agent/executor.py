import subprocess
from typing import Dict, List
from .models.models import ExecuteResponse


def execute_command(command: List[str], timeout: int = 30) -> List[ExecuteResponse]:
    """
    subprocess.run을 사용해 커맨드를 실행하고 결과를 반환
    Args:
        command: 실행할 커맨드 문자열
        timeout: 실행 제한 시간(초)
    Returns:
        stdout, stderr, returncode 또는 에러 메시지를 포함한 딕셔너리
    """

    results: List[ExecuteResponse] = []
    for cmd in command:
        try:
            result = subprocess.run(
                cmd,
                shell=True,  # 주의: 화이트리스트 검증 필수
                capture_output=True,
                text=True,
                timeout=timeout
            )
            results.append(ExecuteResponse(
                command=cmd,
                stdout=result.stdout,
                stderr=None,
                returncode=result.returncode
            ))

        except subprocess.TimeoutExpired:
            results.append(ExecuteResponse(
                command=cmd,
                stdout=None,
                stderr=f"{timeout}s timeout",
                returncode=1
            ))
        except subprocess.SubprocessError as e:
            results.append(ExecuteResponse(
                command=cmd,
                stdout=None,
                stderr=str(e),
                returncode=1))

    return results