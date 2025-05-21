from fastapi import FastAPI, HTTPException
from server.models.models import Alarm, ExecuteRequest, ExecuteResponse
import requests
from server.config import API_TOKEN
from server.workflow.state import AgentState
from server.workflow.builder import build_workflow
from typing import List, Dict
from server.utils.logging import setup_logger

app = FastAPI()
cloudwatch_messages: List[Dict] = []
logger = setup_logger(__name__)
last_question_bool = False

def sqs_trigger(alarm: Alarm):
    """CloudWatch SQS 메시지 처리."""
    workflow = build_workflow()
    initial_state = AgentState(
        input_type="cloudwatch",
        raw_input=alarm.dict(),
        command=None,
        target=None,
        approved=True,
        execution_result=None,
        final_answer=None,
        chat_history=[],
        intent=None,
        user_question=False
    )
    
    cloudwatch_messages.append(workflow.invoke(initial_state))

@app.post("/sqs_trigger")
def sqs_trigger_endpoint(alarm: Alarm):
    sqs_trigger(alarm)

@app.get("/commands")
def get_commands() -> List[Dict]:
    """cloudwatch_messages 조회."""
    return cloudwatch_messages

@app.post("/chat")
def handle_chat(request:Dict):
    """Streamlit 사용자 입력 처리."""
    global last_question_bool
    logger.info(f"Received request: {request}")
    user_input = request.get("user_input")
    chat_history = request.get("chat_history")
    workflow = build_workflow()
    initial_state = AgentState(
        input_type="streamlit",
        raw_input={"user_input": user_input},
        command=None,
        target=None,
        approved=False,
        execution_result=None,
        final_answer=None,
        chat_history=chat_history,
        intent=None,
        user_question=last_question_bool
    )
    result = workflow.invoke(initial_state)
    if not last_question_bool and result["user_question"]:
        last_question_bool = True
    elif result["user_question"] and last_question_bool:
        last_question_bool = False

    return result["final_answer"]

@app.post("/execute", response_model=List[ExecuteResponse])
def handle_execute(request: Dict) -> List[ExecuteResponse]:
    """Agent의 /execute API 호출로 커맨드 실행.
    
    Args:
        request: 명령어와 에이전트 정보 포함
    Returns:
        실행 결과 리스트
    """

    commands = request.get("command")
    target = request.get("agent")
    url = request.get("url")
    logger.info(f"commands: {commands}, target: {target}, url: {url}")
    
    if not commands:
        logger.warning("No command provided in request")
        return [ExecuteResponse(
            command="",
            stdout=None,
            stderr="No command to execute",
            returncode=1
        )]

    try:
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        payload = ExecuteRequest(command=commands, agent=target)
        logger.info(f"Sending request to {url}/execute with command: {commands}")
        response = requests.post(f"{url}/execute", json=payload.dict(), headers=headers)
        response.raise_for_status()

        logger.info(f"Response: {response.json()}")
        
        # 응답이 List[ExecuteResponse]와 호환되는지 확인
        results = response.json()
        if not isinstance(results, list):
            logger.error(f"Expected list response, got: {type(results)}")
            return [ExecuteResponse(
                command=" ".join(commands) if commands else "",
                stdout=None,
                stderr="Invalid response format from agent",
                returncode=1
            )]
        
        # Pydantic 모델로 변환
        return [ExecuteResponse(**result) for result in results]
    
    except requests.RequestException as e:
        logger.error(f"Request to agent failed: {str(e)}")
        return [ExecuteResponse(
            command=" ".join(commands) if commands else "",
            stdout=None,
            stderr=f"Request failed: {str(e)}",
            returncode=1
        )]

@app.get("/test/inject_message")
def inject_test_message():
    """테스트 알람 주입."""
    test_alarm_data = {
        "AlarmName": "alt_cpu_high_alert",
        "AlarmDescription": None,
        "AWSAccountId": "467860137194",
        "AlarmConfigurationUpdatedTimestamp": "2025-05-13T09:50:08.366+0000",
        "NewStateValue": "ALARM",
        "NewStateReason": "Threshold Crossed: 1 out of the last 1 datapoints [94.10166666666666 (14/05/25 01:55:00)] was greater than or equal to the threshold (90.0) (minimum 1 datapoint for OK -> ALARM transition).",
        "StateChangeTime": "2025-05-14T01:58:11.589+0000",
        "Region": "US East (Ohio)",
        "AlarmArn": "arn:aws:cloudwatch:us-east-2:467860137194:alarm:alt_cpu_high_alert",
        "OldStateValue": "OK",
        "OKActions": [],
        "AlarmActions": ["arn:aws:sns:us-east-2:467860137194:ATL_sns.fifo"],
        "InsufficientDataActions": [],
        "Trigger": {
            "MetricName": "CPUUtilization",
            "Namespace": "AWS/EC2",
            "StatisticType": "Statistic",
            "Statistic": "MAXIMUM",
            "Unit": None,
            "Dimensions": [{"value": "i-08fb8abe21e6fa058", "name": "InstanceId"}],
            "Period": 60,
            "EvaluationPeriods": 1,
            "DatapointsToAlarm": 1,
            "ComparisonOperator": "GreaterThanOrEqualToThreshold",
            "Threshold": 90.0,
            "TreatMissingData": "missing",
            "EvaluateLowSampleCountPercentile": ""
        }
    }
    alarm = Alarm(raw_data=test_alarm_data)
    sqs_trigger(alarm)