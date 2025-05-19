# utils/server_info.py
from fastapi import HTTPException

my_server_list = [
    {
        "uuid": "i-08fb8abe21e6fa058",
        "ip": "3.128.204.185",
        "name": "agent-1",
    },
]

def get_agent_url(instance_id: str, port: str = "9917") -> str:
    """instance_id로 my_server_list에서 IP 조회, AGENT_URL 생성."""
    for server in my_server_list:
        if server["uuid"] == instance_id:
            return f"http://{server['ip']}:{port}"
    raise HTTPException(status_code=400, detail=f"Instance ID {instance_id} not found in server list")