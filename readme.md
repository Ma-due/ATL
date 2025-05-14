### 시스템 아키텍처
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
       [LLM (Command Suggestion)]  [SSM (Command Execution)]
                  |                         |
                  v                         v
       [User Interface] <-> [EC2 Command Results]
```