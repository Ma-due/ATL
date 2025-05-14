from fastapi import FastAPI
from .wermodels.alarm import Alarm
import json

app = FastAPI()
messages = []

# 테스트용 메시지
TEST_ALARM_DATA = {
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

def sqs_trigger(alarm: Alarm):
    global messages
    messages.append(alarm.dict())
    messages = messages[-100:]
    print(f"Received alarm data: {alarm.raw_data['AlarmName']}")
    return {"status": "received"}

@app.post("/sqs_trigger")
def sqs_trigger_endpoint(alarm: Alarm):
    return sqs_trigger(alarm)

@app.get("/messages")
def get_messages():
    return {"messages": messages}

@app.get("/test/inject_message")
def inject_test_message():
    alarm = Alarm(raw_data=TEST_ALARM_DATA)
    result = sqs_trigger(alarm)
    print(f"Injected test alarm: {alarm.raw_data['AlarmName']}")
    return {"status": "test message injected", "sqs_trigger_result": result}

@app.post("/chat")
def chat_endpoint(data: dict):
    message = data.get("message", "")
    print(f"Received chat message: {message}")
    # 더미 LLM 응답
    response = f"Dummy LLM response for: {message}"
    return {"response": response}