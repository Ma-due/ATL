import boto3
import json
import requests
from models.alarm import Alarm
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_SQS_QUEUE_URL, FASTAPI_HOST, FASTAPI_PORT

# SQS 클라이언트 초기화
sqs = boto3.client(
    'sqs',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

fastapi_url = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}/sqs_trigger"

def poll_sqs():
    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=AWS_SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20
            )
            messages = response.get('Messages', [])
            if not messages:
                print("No messages received in this poll.")
                continue
            for message in messages:
                try:
                    # SNS 메시지 파싱
                    sns_message = json.loads(message['Body'])
                    # CloudWatch 알람 데이터 파싱
                    alarm_data = json.loads(sns_message['Message'])
                    # Alarm 모델로 래핑
                    alarm = Alarm(raw_data=alarm_data)
                    # FastAPI에 전송 (인증 제거)
                    response = requests.post(fastapi_url, json=alarm.dict())
                    if response.status_code == 200:
                        print(f"Sent alarm data to FastAPI")
                        sqs.delete_message(QueueUrl=AWS_SQS_QUEUE_URL, ReceiptHandle=message['ReceiptHandle'])
                        print("Message deleted from queue.")
                    else:
                        print(f"Failed to send to FastAPI: {response.text}")
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {e}")
                except Exception as e:
                    print(f"Error processing message: {e}")
        except Exception as e:
            print(f"Error polling SQS: {e}")

if __name__ == "__main__":
    if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SQS_QUEUE_URL]):
        raise ValueError("Missing AWS credentials or SQS_QUEUE_URL in .env")
    print("Starting SQS poller...")
    print(f"Using SQS Queue URL: {AWS_SQS_QUEUE_URL}")
    print(f"Region: {AWS_REGION}")
    poll_sqs()