import streamlit as st

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    st.title("登入頁面")
    username = st.text_input("帳號")
    password = st.text_input("密碼", type="password")
    if st.button("登入"):
        if username == "user" and password == "pass":
            st.session_state.authenticated = True
            st.session_state.username = username
            st.success("登入成功")
            st.experimental_rerun()
        else:
            st.error("帳號或密碼錯誤")

if not st.session_state.authenticated:
    login()
else:
    st.write(f"歡迎 {st.session_state.username}！")
