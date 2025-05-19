# server/utils/logging.py
import logging

def setup_logger(name: str) -> logging.Logger:
    """로거 설정 및 반환 (콘솔 출력 전용)."""
    logger = logging.getLogger(name)
    if logger.handlers:  # 이미 설정된 경우 재설정 방지
        return logger

    logger.setLevel(logging.DEBUG)

    # 포맷 설정
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger