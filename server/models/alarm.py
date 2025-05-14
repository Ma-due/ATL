from pydantic import BaseModel

class Alarm(BaseModel):
    raw_data: dict  # 원본 JSON 데이터