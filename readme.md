## 시스템 아키텍처
```
[EC2 Instances] -> [CloudWatch Metrics] -> [CloudWatch Alarm]
   |                                         |
   v                                         v
                [SNS Topic] -> [SQS Queue]
                           |
                           v
                [LangGraph Server (FastAPI)] 
                           |
                           v
       [LLM (Command Suggestion)]  [Agent (API/Subprocess)]
                  |                         |
                  v                         v
       [User Interface] <-> [EC2 Command Results]
```

## 파일 구조
```
ATL/
├── app/
│   ├── main.py         # Streamlit 챗봇 UI, 사용자 입력을 /chat으로 전송
│   ├── .env           # Streamlit 환경 변수 (FastAPI 호스트/포트)
│   ├── config.py      # Streamlit 설정 로드 (환경 변수 관리)
├── server/
│   ├── main.py        # FastAPI 백엔드, API 엔드포인트
│   ├── .env           # FastAPI 환경 변수 (AWS, FastAPI 설정)
│   ├── models/
│   │   ├── alarm.py   # 알람 데이터 모델 (Pydantic)
│   ├── sqs_puller.py  # SQS 큐 폴링, /sqs_trigger로 알람 전달
│   ├── config.py      # FastAPI 설정 로드 (환경 변수 관리)
├── agent/
│   ├── .env           # 에이전트 환경 변수 (API 토큰, FastAPI 설정)
│   ├── config.py      # 에이전트 설정 로드 (환경 변수 관리)
│   ├── main.py        # 에이전트 API 서버, 명령 실행 엔드포인트
│   ├── security.py    # API 요청 인증 및 보안 처리
│   ├── error_handler.py # 에이전트 예외 처리 및 오류 로깅
│   ├── executor.py    # 명령 실행 (subprocess 호출)
```

## LangGraph 구현 ToDo 항목

### 1. SQS 메시지 분석 및 리눅스 커맨드 생성
- **1.1. LangGraph 워크플로우 파일 생성**
  - `server/workflow.py` 생성, LangGraph 워크플로우 정의 (`AgentState`, `analyze` 노드).
- **1.2. FastAPI에서 LangGraph 호출**
  - `server/main.py` 수정, `/sqs_trigger`에서 워크플로우 호출, 커맨드 생성.
- **1.3. 메시지 저장 구조 구현**
  - `server/main.py`에 `messages` 리스트 추가, 알람 및 커맨드 저장.
- **1.4. Streamlit에서 커맨드 제안**
  - `app/main.py` 수정, `/messages` 호출, 채팅창에 커맨드 제안 표시.

### 2. 커맨드 실행
- **2.1. Streamlit에서 커맨드 수락 UI**
  - `app/main.py`에 수락 버튼 추가, `/execute`로 커맨드 전송.
- **2.2. FastAPI에 실행 엔드포인트 추가**
  - `server/main.py`에 `/execute` 추가, 에이전트 API 호출.
- **2.3. 에이전트에서 커맨드 실행**
  - `agent/main.py`, `agent/executor.py` 수정, `subprocess`로 커맨드 실행.

### 3. 결과 분석 및 다음 스텝 제안
- **3.1. LangGraph에 결과 분석 노드 추가**
  - `server/workflow.py`에 `execute`, `analyze_result` 노드 추가, 결과 분석 및 커맨드 제안.