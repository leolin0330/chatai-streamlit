import streamlit as st
from openai import OpenAI, OpenAIError
from datetime import date

# ========= 頁面基本設定 =========
st.set_page_config(page_title="問答助手", page_icon="💬")

# ========= 初始化 session state =========
for key, default in {
    "authenticated": False,
    "username": None,
    "chat_history": [],
    "confirm_clear": False,
    "daily_usage": {}
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ========= 密碼驗證機制 =========
VALID_PASSWORDS = st.secrets["passwords"]

def login():
    st.title("登入頁面")
    with st.form("login_form"):
        username = st.text_input("帳號")
        password = st.text_input("密碼", type="password")
        submitted = st.form_submit_button("登入")

        if submitted:
            if username in VALID_PASSWORDS and password == VALID_PASSWORDS[username]:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("登入成功")
                st.rerun()
            else:
                st.error("帳號或密碼錯誤")

# 未登入時顯示登入表單
if not st.session_state.authenticated or not st.session_state.username:
    login()
    st.stop()

# ========= 通過驗證，載入主頁功能 =========
username = st.session_state.username
st.success(f"歡迎 {'ASSHOLE BING 🙂' if username == 'abing' else username}！")

# OpenAI 設定
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# 每日使用金額限制
DAILY_LIMITS = {
    "ahong": None,
    "abing": 0.05,
    "user": 0.05,
}
user_limit = DAILY_LIMITS.get(username, 0.05)
today = str(date.today())
today_used = st.session_state.daily_usage.get(today, 0.0)
remaining = round(user_limit - today_used, 4) if user_limit is not None else None

# 顯示使用情況提示
if username == "ahong":
    st.info("🛠️ 你是管理員，無金額限制")
else:
    st.warning(f"⚠️ 今日已使用：${round(today_used, 4)}，剩餘：${remaining} 美元")
    if remaining is not None and remaining <= 0:
        st.error("🚫 今日已達金額上限，請明天再來或聯絡管理員。")
        st.stop()

# ========= 問答函式 =========
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

# ========= CSS 美化 =========
st.markdown("""
    <style>
    .chat-container {
        margin-top: 50px;
    }
    .chat-bubble-user {
        background-color: #DCF8C6;
        padding: 10px 15px;
        border-radius: 15px;
        margin: 12px 0 12px 10px;
        max-width: 75%;
        align-self: flex-start;
    }
    .chat-bubble-bot {
        background-color: #F1F0F0;
        padding: 10px 15px;
        border-radius: 15px;
        margin: 12px 10px 12px 0;
        max-width: 75%;
        align-self: flex-end;
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

# ========= 對話紀錄顯示 =========
st.markdown("### 📝 對話紀錄")
with st.container():
    for chat in st.session_state.chat_history:
        # 使用者訊息（靠左）
        st.markdown(
            f"""
            <div style='display: flex; justify-content: flex-start; margin-bottom: 5px;'>
                <div style='background-color: #DCF8C6; padding: 12px 18px; border-radius: 15px; max-width: 90%; word-wrap: break-word;'>
                    {chat["question"]}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # AI 回覆訊息（靠右）
        st.markdown(
            f"""
            <div style='display: flex; justify-content: flex-end; margin-bottom: 5px;'>
                <div style='background-color: #F1F0F0; padding: 12px 18px; border-radius: 15px; max-width: 90%; word-wrap: break-word;'>
                    {chat["answer"]}
                </div>
            </div>
            <div style='text-align: right; font-size: 12px; color: gray; margin-bottom: 30px;'>
                {chat["meta"]}
            </div>
            """, unsafe_allow_html=True)

# ========= 對話輸入表單 =========
with st.form("chat_form", clear_on_submit=True):
    cols = st.columns([6, 2, 2])
    with cols[0]:
        user_input = st.text_input("💡 請輸入你的問題：")
    with cols[1]:
        submitted = st.form_submit_button("送出")
    with cols[2]:
        clear_clicked = st.form_submit_button("🗑️ 清除")

if submitted and user_input:
    answer, tokens, usd_cost, twd_cost = ask_openai(user_input)
    st.session_state.chat_history.append({
        "question": user_input,
        "answer": answer,
        "meta": f"🧾 使用 Token 數：{tokens}    💵 估算費用：${usd_cost} 美元（約 NT${twd_cost}）"
    })
    st.session_state.daily_usage[today] = st.session_state.daily_usage.get(today, 0.0) + usd_cost
    st.rerun()

# ========= 清除功能 =========
if clear_clicked:
    st.session_state.confirm_clear = True

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

# ========= 使用記錄展開顯示 =========
with st.expander("📊 每日使用紀錄"):
    for date_str, cost in sorted(st.session_state.daily_usage.items()):
        st.write(f"{date_str}：${round(cost, 4)}")
