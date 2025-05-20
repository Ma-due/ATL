import streamlit as st
import requests
from config import FASTAPI_HOST, FASTAPI_PORT


chat_url = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}/chat"

st.title("ATL")
st.caption("EC2 모니터링 챗봇")

# 초기 상태 설정
if 'session_history' not in st.session_state:
    st.session_state.session_history = []

# 채팅창
chat_placeholder = st.empty()
with chat_placeholder.container():
    for entry in st.session_state.session_history:
        with st.chat_message("user"):
            st.write(entry["user_messages"])
        with st.chat_message("ai"):
            final_answer = entry.get("final_answer", {})
            response = final_answer.get("response", "No response")
            if "error" in final_answer:
                response = final_answer["error"]
            st.write(response)

# 사용자 입력 처리
if user_question := st.chat_input(placeholder="질문 내용 입력"):
    with st.chat_message("user"):
        st.write(user_question)

    with st.spinner("답변을 생성하는 중"):
        try:
            print(f"Sending request to server: {user_question}")
            response = requests.post(chat_url, json={"user_input": user_question, "chat_history": st.session_state.session_history})
            response.raise_for_status()
            ai_message = response.json()
        except requests.RequestException as e:
            ai_message = {"error": f"Failed to get response: {str(e)}"}

        # AI 응답 표시
        with st.chat_message("ai"):
            response_text = ai_message.get("response", "No response")
            if "error" in ai_message:
                response_text = ai_message["error"]
            st.write(response_text)

        # session_history에 딕셔너리 형태로 추가
        st.session_state.session_history.append(
            {
                "user": {
                    "content": user_question,
                },
                "assistant": {
                    "content": response_text,
                },
            },
        )

        print(f"Conversation response: {ai_message}")