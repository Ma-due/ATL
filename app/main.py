import streamlit as st
import requests
from config import FASTAPI_HOST, FASTAPI_PORT

# FastAPI URL
chat_url = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}/chat"

# Streamlit UI
st.title("ATL")
st.caption("EC2 모니터링 챗봇")

# 초기 상태 설정
if 'message_list' not in st.session_state:
    st.session_state.message_list = []
if 'last_message_count' not in st.session_state:
    st.session_state.last_message_count = 0

# 채팅창
chat_placeholder = st.empty()
with chat_placeholder.container():
    for message in st.session_state.message_list:
        with st.chat_message(message["role"]):
            st.write(message["content"])

# 사용자 입력 처리
if user_question := st.chat_input(placeholder="질문 내용 입력"):
    with st.chat_message("user"):
        st.write(user_question)
    st.session_state.message_list.append({"role": "user", "content": user_question})

    with st.spinner("답변을 생성하는 중"):
        try:
            response = requests.post(chat_url, json={"message": user_question})
            response.raise_for_status()
            ai_message = response.json().get("response", "Error: No response from server")
        except requests.RequestException as e:
            ai_message = f"Error: Failed to get response ({e})"
        with st.chat_message("ai"):
            st.write(ai_message)
        st.session_state.message_list.append({"role": "ai", "content": ai_message})
        print(f"Conversation response: {ai_message}")  # 터미널 출력
