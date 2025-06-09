import streamlit as st
from openai import OpenAI, OpenAIError
from datetime import date
import json
import os
import docx
import PyPDF2

USAGE_FILE = "daily_usage.json"

def load_daily_usage():
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_daily_usage(data):
    try:
        with open(USAGE_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        st.error(f"儲存使用紀錄失敗：{e}")

st.set_page_config(page_title="問答助手", page_icon="💬")

# 初始化 session_state（登入前）
for key, default in {
    "authenticated": False,
    "username": None,
    "confirm_clear": False,
    "daily_usage": {}
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if not st.session_state.daily_usage:
    st.session_state.daily_usage = load_daily_usage()

VALID_PASSWORDS = st.secrets["passwords"]

def login():
    st.title("登入頁面(測試區)")
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

if not st.session_state.authenticated or not st.session_state.username:
    login()
    st.stop()

username = st.session_state.username

# 初始化個別用戶的 chat_history
chat_key = f"chat_history_{username}"
if chat_key not in st.session_state:
    st.session_state[chat_key] = []

# 登出
if st.button("登出"):
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()
    st.stop()

st.title("這是測試區")
st.success(f"歡迎 {'ASSHOLE BING 🙂' if username == 'abing' else username}！")

api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

DAILY_LIMITS = {
    "ahong": None,
    "abing": 0.05,
    "user": 0.05,
}
user_limit = DAILY_LIMITS.get(username, 0.05)
today = str(date.today())
today_used = st.session_state.daily_usage.get(today, 0.0)
remaining = round(user_limit - today_used, 4) if user_limit is not None else None

if username == "ahong":
    st.info("🛠️ 你是管理員，無金額限制")
else:
    st.warning(f"⚠️ 今日已使用：${round(today_used, 4)}，剩餘：${remaining} 美元")
    if remaining is not None and remaining <= 0:
        st.error("🚫 今日已達金額上限，請明天再來或聯絡管理員。")
        st.stop()

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

st.markdown("""
<style>
.chat-container { margin-top: 50px; }
.chat-bubble-user { background-color: #DCF8C6; padding: 10px 15px; border-radius: 15px; margin: 12px 0 12px 10px; max-width: 75%; align-self: flex-start; }
.chat-bubble-bot { background-color: #F1F0F0; padding: 10px 15px; border-radius: 15px; margin: 12px 10px 12px 0; max-width: 75%; align-self: flex-end; }
.chat-meta { font-size: 13px; color: #666; margin-top: -10px; margin-bottom: 20px; text-align: right; }
div[data-testid="stForm"] { margin-top: 100px; }
</style>
""", unsafe_allow_html=True)

st.markdown("### 📝 對話紀錄")

# ========= 顯示對話紀錄 =========
with st.container():
    for chat in st.session_state[chat_key]:
        st.markdown(f'''
            <div style="font-size:13px; color:#555; margin-left:8px; margin-bottom:3px;">
                <b>{'👤 ASSHOLE BING' if username == 'abing' else '👤 使用者'}</b>
            </div>
            <div style="background:#DCF8C6; padding:10px; border-radius:15px; max-width:75%; margin-bottom:10px;">
                {chat["question"]}
            </div>''', unsafe_allow_html=True)
        st.markdown(f'''
            <b><div style="font-size:13px; color:#555; text-align:right; margin-right:8px; margin-bottom:5px;">
                🤖 助手
            </div></b>
            <div style="background:#F1F0F0; padding:10px 15px; border-radius:15px; max-width:75%; margin-left:auto; margin-bottom:10px;">
                {chat["answer"]}
            </div>''', unsafe_allow_html=True)
        st.markdown(f'''
            <div style="font-size:13px; color:#666; text-align:right; margin-bottom:20px;">
                {chat["meta"]}
            </div>
            <hr style="border: none; border-top: 1px dashed #ccc; margin: 15px 0;">
            ''', unsafe_allow_html=True)

# ========= 對話輸入表單 =========
with st.form("chat_form", clear_on_submit=True):
    cols = st.columns([6, 2])
    with cols[0]:
        user_input = st.text_input("💡 請輸入你的問題：")
        uploaded_file = st.file_uploader("📁 上傳檔案（可選）", type=["txt", "pdf", "docx"])
    with cols[1]:
        submitted = st.form_submit_button("送出")

clear_clicked = st.button("清除紀錄")

# ==== 初始化記憶檔案內容用的 session_state ====
if "uploaded_file_text" not in st.session_state:
    st.session_state.uploaded_file_text = None
    st.session_state.uploaded_file_name = None

if submitted:
    full_prompt = user_input.strip()

    # 如果有上傳新檔案，就重新解析並記下內容
    if uploaded_file:
        file_text = ""

        if uploaded_file.name.endswith(".txt"):
            file_text = uploaded_file.read().decode("utf-8", errors="ignore")

        elif uploaded_file.name.endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            file_text = "\n".join([page.extract_text() or "" for page in pdf_reader.pages])

        elif uploaded_file.name.endswith(".docx"):
            doc = docx.Document(uploaded_file)
            file_text = "\n".join([para.text for para in doc.paragraphs])

        else:
            st.warning("❌ 不支援的檔案格式，目前僅支援 .txt、.pdf、.docx")
            file_text = None

        if file_text:
            # 記住檔案內容和名稱
            st.session_state.uploaded_file_text = file_text
            st.session_state.uploaded_file_name = uploaded_file.name
            st.info("📖 檔案內容已成功讀取，現在可以根據這份文件問問題")

    # 判斷是要送出單純問題，還是附加檔案的 prompt
    if user_input:
        if st.session_state.uploaded_file_text:
            prompt_with_file = f"以下是使用者的檔案內容：\n\n{st.session_state.uploaded_file_text}\n\n問題：{user_input}"
            question_desc = f"{user_input}\n（來自上傳檔案：{st.session_state.uploaded_file_name}）"
        else:
            prompt_with_file = user_input
            question_desc = user_input

        answer, tokens, usd_cost, twd_cost = ask_openai(prompt_with_file)

        st.session_state[chat_key].append({
            "question": question_desc,
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
            st.session_state[chat_key] = []
            st.session_state.confirm_clear = False
            st.rerun()
    with c2:
        if st.button("❌ 取消"):
            st.session_state.confirm_clear = False

# ========= 使用記錄 =========
with st.expander("📊 每日使用紀錄"):
    for date_str, cost in sorted(st.session_state.daily_usage.items()):
        st.write(f"{date_str}：${round(cost, 4)}")



 # streamlit run "C:\Users\timmy\PycharmProjects\PythonProject\LLM\ChatGPT_office_answer.py"
git add chat_ai_test.py
git commit -m "更新chat_ai_test.py功能"
git pull origin main
git push origin main
