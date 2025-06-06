import streamlit as st
from openai import OpenAI, OpenAIError

# =====🔐 密碼驗證功能區塊 =====
VALID_PASSWORDS = st.secrets["passwords"]

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 請先登入")
    username = st.text_input("帳號：")
    password = st.text_input("密碼：", type="password")
    if st.button("登入"):
        if username in VALID_PASSWORDS and password == VALID_PASSWORDS[username]:
            st.session_state.authenticated = True
            st.success("✅ 登入成功！")
            st.rerun()
        else:
            st.error("❌ 帳號或密碼錯誤")
    st.stop()

# =====✅ 通過驗證，進入主頁 =====
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

st.set_page_config(page_title="問答助手", page_icon="💬")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = False

# 回答函式
def ask_openai(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一位樂於助人的助理。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        answer = response.choices[0].message.content.strip()
        tokens_used = response.usage.total_tokens
        usd_cost = round(tokens_used * 0.01 / 1000, 6)
        twd_cost = round(usd_cost * 32, 4)
        return answer, tokens_used, usd_cost, twd_cost
    except OpenAIError as e:
        return f"❌ API 錯誤：{str(e)}", 0, 0.0, 0.0

# CSS
st.markdown("""
    <style>
    .chat-container {
        margin-top: 50px;
    }
    .chat-bubble-user {
        background-color: #DCF8C6;
        padding: 10px 15px;
        border-radius: 15px;
        margin: 10px 0;
        max-width: 75%;
        align-self: flex-start;
    }
    .chat-bubble-bot {
        background-color: #F1F0F0;
        padding: 10px 15px;
        border-radius: 15px;
        margin: 10px 0;
        max-width: 75%;
        align-self: flex-end;
        margin-left: auto;
    }
    .chat-meta {
        font-size: 13px;
        color: #666;
        margin-top: -10px;
        margin-bottom: 20px;
        text-align: right;
    }
    div[data-testid="stForm"] {
        margin-top: 100px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💬 問答助手")

# ✅ 聊天紀錄區
st.markdown("## 📝 對話紀錄")
with st.container():
    for chat in st.session_state.chat_history:
        st.markdown(f'<div class="chat-bubble-user">{chat["question"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-bubble-bot">{chat["answer"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-meta">{chat["meta"]}</div>', unsafe_allow_html=True)

# ✅ 輸入表單（送出按鈕）單獨放
with st.form("chat_form", clear_on_submit=True):
    cols = st.columns([7, 2])
    with cols[0]:
        user_input = st.text_input("💡 請輸入你的問題：")
    with cols[1]:
        submitted = st.form_submit_button("送出")

if submitted and user_input:
    answer, tokens, usd_cost, twd_cost = ask_openai(user_input)
    st.session_state.chat_history.append({
        "question": user_input,
        "answer": answer,
        "meta": f"🧾 使用 Token 數：{tokens}    💵 估算費用：${usd_cost} 美元（約 NT${twd_cost}）"
    })
    st.rerun()

# ✅ 清除按鈕獨立放，才不會被表單 reset 狀態
if st.button("🗑️ 清除"):
    st.session_state.confirm_clear = True

# ✅ 清除確認區塊
if st.session_state.confirm_clear:
    st.warning("⚠️ 你確定要清除所有對話紀錄嗎？這個動作無法還原！")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ 是的，清除"):
            st.session_state.chat_history = []
            st.session_state.confirm_clear = False
            st.rerun()
    with c2:
        if st.button("❌ 取消"):
            st.session_state.confirm_clear = False
