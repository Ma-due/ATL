# AI BOOTCAMP 2기 프로젝트

## 프로젝트 기획 의도
사내(혹은 Cloud 부문)에서 적극 추진 중인 NPO를 달성하기 위해서는,
일반적인 Streamlit 등 채팅 기반의 (사용자 선 입력 <-> LLM 응답) 구조가 아닌 외부 시스템에서 AI가 트리거되어 선제적인 처리 및 대응을 해줄 수 있는 시스템을 고안하고자 함

- **목적**: 모니터링 시스템 기반 Alert 발생 시 해당 서버에 상태 점검을 위한 커맨드를 실행 -> 결과를 분석/요약하여 사용자에게 제공하며, 사용자 요청에 따른 커맨드를 생성 및 실행
- **사용 사례**: 서버 상태 모니터링, 알람 기반 워크플로우 자동화.

## 시스템 아키텍처
![아키텍처](https://github.com/user-attachments/assets/39420dc1-02f8-480c-b51d-1f922a6334a0)

- **CloudWatch, SNS, SQS**
    - 시스템 모니터링 및 전파 체계를 갈음
    - EC2 Metrics -> Cloudwatch Alarm -> SNS -> SQS -> Server
- **Streamlit**
    - Jira, Serviceflow 등 티켓 기반 처리 시스템 갈음
    - 시간 제약 및 개발 편의성으로 인해 Streamlit 선정
    - 채팅 기반으로 메시지 조회 및 커맨드 실행 승인 여부 결정하도록 로직 변경
- **Server**
    - 백엔드 Endpoint를 위한 FastAPI, Langgraph 로직을 수행
- **Agent**
    -  실 서버에 배포 될 Linux Command 실행 가능한 Agent
    -  시간 제약 및 개발 편의성으로 인해 FastAPI를 통한 HTTP 통신으로 Command 수신

## Langgraph Workflow
### Langgraph 아키텍처
![Langgraph진행](https://github.com/user-attachments/assets/7316c5e9-03d7-4bb7-bd32-5c95908ebbfb)
 - **Node 리스트**
    - `receive` : 사용자의 입력을 수신하여 이전 대화를 분석하여 전처리하고, 다음 진행 노드 분기 처리
    - `generate` : 사용자/Cloudwatch Alarm 메시지 기반 시스템 분석을 위한 Linux Command 생성
    - `execute` : 사용자의 실행 여부에 따라 대상 서버에 Command 실행 명령
    - `analyze` : Command 수행 결과 기반 시스템 분석 및 요약
    - `fetch` : Streamlit 채팅 기반 시스템 전환으로 인해 사용자가 채팅을 통해 생성된 티켓(Cloudwatch Alarm 메시지)를 조회

### Input 인입점에 따른 노드 진행
- Streamlit(사용자 요청)
    - 사용자의 채팅을 Source 데이터로 사용 -> `receive` 노드로 진행
    - `receive` 노드에서 사용자의 질문을 분석(알람 티켓 조회, Command 생성 요청, 생성된 커맨드에 대한 실행 승인 여부) 하여 적절한 노드로 라우팅
    - 알람 티켓 조회 -> `fetch` 노드로 이동, 생성되어 있는 알람 티켓에 대한 정보 표시
    - Command 생성 요청 -> `generate` 노드가 사용자가 요청한 의도를 달성할 수 있는 적절한 Linux Command를 생성
    - 실행 승인 여부 -> (Y) : 실행 / (N) : 중단
    - Graph의 진행 상황에 따라 적절한 답변을 `analyze` 노드에서 생성

- Cloudwatch(특정 조건 트리거 기반)
    - Alarm 시스템에서 Alarm 메시지를 Source 데이터로 사용 -> `receive` 노드로 이동
    - Alarm 메시지는 독립적이며 항상 최초의 메시지기 때문에 `generate` 노드로 이동
    - 현재 받은 메시지 기반 서버의 상태를 분석하기 위한 Command를 조회, 단순 조회성 Command만 생성하므로 최초 1회 -> `execute` 노드로 이동
    - 생성된 커맨드를 실행하고 결과를 수합해 `analyze` 노드로 이동
    - 별도의 티켓 저장소에 저장

## 시나리오 기반 시연
<div style="overflow-x: auto; white-space: nowrap; padding: 10px; display: flex; flex-wrap: nowrap; min-width: 2000px;">
  <img src="https://github.com/user-attachments/assets/7316c5e9-03d7-4bb7-bd32-5c95908ebbfb" alt="Workflow Trigger" style="width: 300px; height: auto; display: inline-block; margin-right: 10px;"> <!-- 워크플로우 트리거 -->
  <img src="https://github.com/user-attachments/assets/7316c5e9-03d7-4bb7-bd32-5c95908ebbfb" alt="Workflow Trigger" style="width: 300px; height: auto; display: inline-block; margin-right: 10px;"> <!-- 워크플로우 트리거 -->
  <img src="https://github.com/user-attachments/assets/7316c5e9-03d7-4bb7-bd32-5c95908ebbfb" alt="Workflow Trigger" style="width: 300px; height: auto; display: inline-block; margin-right: 10px;"> <!-- 워크플로우 트리거 -->
  <img src="https://github.com/user-attachments/assets/7316c5e9-03d7-4bb7-bd32-5c95908ebbfb" alt="Workflow Trigger" style="width: 300px; height: auto; display: inline-block; margin-right: 10px;"> <!-- 워크플로우 트리거 -->
  <img src="https://github.com/user-attachments/assets/7316c5e9-03d7-4bb7-bd32-5c95908ebbfb" alt="Workflow Trigger" style="width: 300px; height: auto; display: inline-block; margin-right: 10px;"> <!-- 워크플로우 트리거 -->
  <img src="https://hackmd.io/_Uploads/rJp_5U2blg.png" alt="CloudWatch Alert" style="width: 300px; height: auto; display: inline-block; margin-right: 10px;"> <!-- 알람 발생 -->
</div>

## 파일 구조 및 기능
```
ATL/
├── server/                  - 백엔드 FastAPI 서버
│   ├── utils/                 - 유틸리티 모듈
│   │   ├── server_info.py       - 서버 정보 (구성 정보 시스템 가정)
│   │   ├── llm.py               - OpenAI API 클라이언트 초기화
│   │   └── logging.py                
│   ├── workflow/              - LangGraph 워크플로우 정의 및 노드
│   │   ├── builder.py           - Workflow 구성
│   │   ├── state.py             - AgentState 클래스 정의 
│   │   └── nodes/               - Workflow Nodes
│   │       ├── analyze.py         - 실행 결과 분석 및 보고서 생성
│   │       ├── receive.py         - 입력을 통한 분기
│   │       ├── generate.py        - 커맨드 생성 
│   │       ├── fetch.py           - Cloudwatch 메시지 조회
│   │       └── execute.py         - 커맨드 실행 
│   ├── models/                  - 스키마 정의
│   │   └── models.py              - 스키마 정의
│   ├── main.py                - FastAPI 서버, 엔드포인트
│   ├── .env                         
│   ├── config.py                     
│   └── sqs_puller.py          - SQS 메시지 폴링
├── agent/                   - Agent (EC2 배포)
│   ├── models/                - 스키마 정의
│   │   └── models.py              - 스키마 정의  
│   ├── main.py                - FastAPI 서버 
│   ├── executor.py            - 커맨드 실행기
│   ├── security.py            - 커맨드 블랙 리스트 검증 
│   ├── .env                         
│   ├── config.py                    
│   └── error_handler.py       - 에이전트 오류 처리 및 로깅
├── app/                     - 프론트엔드(Streamlit)
│   ├── main.py                - 메인 로직
│   ├── .env                         
│   ├── config.py                    
│   └── logging.py                   
├── requirements.txt                 
└── readme.md                        
```


## 마무리
ATL 프로젝트는 CloudWatch 알람을 기반으로 자동화된 워크플로우를 제공하며, 시스템 모니터링과 분석을 효율화합니다. 현재는 MySQL 권한 문제와 Mermaid 렌더링 개선이 필요하며, 향후 Splunk 통합과 프론트엔드 UI(예: React 버튼)를 확장할 계획입니다. 팀원과의 협업을 위해 HackMD와 같은 온라인 마크다운 편집기를 활용하여 README를 지속적으로 개선할 예정입니다.

**기여 방법**:
- GitHub 리포지토리: [링크 추가]
- 문의: [이메일 또는 Slack 채널 추가]
