import time
import streamlit as st
import datetime
from services.db_operation import init_supabase

# 初期化
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "running" not in st.session_state:
    st.session_state.running = False
if "accumulated_time" not in st.session_state:
    st.session_state.accumulated_time = 0  # 累積時間（トータル時間計算に利用）

# 時間をhh:mm:ss表示する関数
def format_time(seconds):
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


sb = st.sidebar
supabase = init_supabase()
# --- 勉強実績をSupabaseに保存する関数 ---
def save_study_record(USER_ID, total_seconds):
    """
    勉強実績をSupabaseの Result テーブルに保存
    """
    today = datetime.date.today().isoformat()

    record = {
        "user_id": USER_ID,
        "date": today,
        "time": int(total_seconds)
    }

    response = (supabase
                .table("Result")
                .insert(record)
                .execute())

    if response.data:
        sb.success("勉強実績を記録しました！")
    else:
        sb.error("勉強実績の記録に失敗しました。")

# --- コールバック関数 ---
def timer_start():
    st.session_state.start_time = time.time()
    st.session_state.running = True
    
def timer_stop():
    if st.session_state.start_time:
        st.session_state.accumulated_time += time.time() - st.session_state.start_time
    st.session_state.running = False

def timer_resume():
    st.session_state.start_time = time.time()
    st.session_state.running = True

def timer_complete():
    """
    記録ボタン：
    ① total_time を確定
    ② Supabase の Result テーブルに保存
    ③ タイマー初期化
    """
    st.session_state.running = False

    if st.session_state.running and st.session_state.start_time:
        st.session_state.accumulated_time += time.time() - st.session_state.start_time

    total_time = st.session_state.accumulated_time

    # --- DB へ保存 ---
    if total_time > 0:
        save_study_record(st.session_state["user_id"] , total_time)
    else:
        st.warning("0秒の記録は保存しません。")
    # todo 1分未満は保存しない、にしても良いかも

    # 初期化
    st.session_state.start_time = None
    st.session_state.accumulated_time = 0
