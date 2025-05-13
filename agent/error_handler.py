import time
from typing import Dict

def handle_execution_error(result: Dict[str, str | int], max_retries: int = 3) -> Dict[str, str | int]:
    """
    subprocess 실행 오류를 처리하고 재시도 로직 적용
    Args:
        result: 실행 결과 딕셔너리
        max_retries: 최대 재시도 횟수
    Returns:
        최종 결과 또는 에러 메시지
    """
    if not result.get("error") and result.get("returncode", 0) == 0:
        return result
    
    retries = 0
    while retries < max_retries:
        if result.get("error", "").startswith("커맨드가"):
            time.sleep(2 ** retries)  # 지수 백오프
            retries += 1
            # 재시도 로직 (execute_command 재호출 필요 시)
            return {"error": f"재시도 {retries} 실패: {result.get('error')}"}
        return {"error": result.get("error") or result["stderr"]}
    
    return {"error": f"최대 재시도 횟수 도달: {result.get('error')}"}