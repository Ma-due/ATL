from fastapi import FastAPI, HTTPException
from .models.models import Alarm, ExecuteRequest
import requests
import uuid
from server.config import API_TOKEN
from server.workflow.state import AgentState
from server.workflow.builder import build_workflow
from typing import List, Dict


app = FastAPI()
cloudwatch_messages: List[Dict] = []

def sqs_trigger(alarm: Alarm):
    """CloudWatch SQS 메시지 처리."""
    workflow = build_workflow()
    initial_state = AgentState(
        workflow_id=str(uuid.uuid4()),
        input_type="cloudwatch",
        raw_input=alarm.dict(),
        parsed_input={},
        messages=[],
        command=None,
        should_execute=None,
        approved=None,
        execution_result=None,
        feedback_data=None
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
def handle_chat(request):
    """Streamlit 사용자 입력 처리."""
    user_input = request.get("message")
    workflow = build_workflow()
    initial_state = AgentState(
        input_type="streamlit",
        raw_input={"text": user_input},
        parsed_input={},
        messages=[],
        command=None,
        should_execute=None,
        approved=None,
        execution_result=None,
        feedback_data=None
    )
    result = workflow.invoke(initial_state)
    return result["messages"]

@app.post("/execute")
def handle_execute(request: ExecuteRequest):
    """Agent의 /execute API 호출로 커맨드 실행."""
    commands = request.command
    agent = request.agent

    if not commands:
        return {"error": "No command to execute"}

    try:
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        payload = {"command": commands, "agent": agent}
        response = requests.post(f"{agent}:9917/execute", json=payload, headers=headers)
        response.raise_for_status()
        return {"results": response.json()}
    except requests.RequestException as e:
        return {"error": str(e)}

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