## 시스템 아키텍처
```
[EC2 Instances] -> [CloudWatch Metrics] -> [CloudWatch Alarm]
   |                                         |
   v                                         v
[LangGraph Server (FastAPI)] <-> [SNS/Lambda] -> [Webhook]
   |             ^
   v             |
[LLM (Command Suggestion)]  [SSM (Command Execution)]
   |                         |
   v                         v
[User Interface] <-> [EC2 Command Results]
```