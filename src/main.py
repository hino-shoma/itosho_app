import streamlit as st
from services.db_operation import google_login
from utility.applay_css import apply_custom_css
from services.submenu import submenu
submenu() # メニュー一覧を表示
st.set_page_config(
    page_title="すきまっくす",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_css("src/data/assets/css/style.css")

# タイトル
st.title("📓すきまっくす📓")
st.markdown("🔥 *すき間時間を最大限に活用しよう！* 🔥")

# ============== ログイン処理=============================
session = google_login()
st.session_state["user_id"] = session["user"]["id"] # セッションにuser_idを入れる

# ============== 資格選択画面 ==============================
from services.db_operation import init_supabase
import json
supabase = init_supabase()


exam_data = json.loads(supabase.table("Learning materials").select("user_id").eq("user_id",str(st.session_state.user_id)).execute().model_dump_json())["data"]
if len(exam_data)==0:
    tabs = st.tabs(["資格を選択", "どんな資格があるか相談したい"])


    from services.db_operation import fetch_data
    select_col_list = ["id","exam_category","exam_name", "exam_date","is_CBT","target_hours"]
    exam_data = fetch_data("qualification", select_col_list)
    category = list({item["exam_category"] for item in exam_data})

    with tabs[0]:
        category_val =st.selectbox("試験カテゴリを選択してください", options=category, key="exam_category", index=None)
        exam_list = list({item["exam_name"] for item in exam_data if item["exam_category"]==st.session_state["exam_category"]})

        exam_name = st.selectbox("試験名を選択してください", options=exam_list,index=None, key="exam_name")
        if exam_name:
            is_CBT = list({item["is_CBT"] for item in exam_data if item["exam_name"]==st.session_state["exam_name"]})
            id = list({item["id"] for item in exam_data if item["exam_name"]==st.session_state["exam_name"]})

            # TODO:これはなんか必要
            if not "exam_id" in  st.session_state:
                st.session_state["exam_id"] = id[0]
            if is_CBT[0]:
                exam_date = st.date_input("この試験はCBT方式なので、試験日を入力してください", key="exam_date",min_value="today")

            else:
                exam_date_list =list({item["exam_date"] for item in exam_data if item["exam_name"]==st.session_state["exam_name"]})
                exam_date = st.selectbox("試験日を選択してください", options=exam_date_list, index=0,key="exam_date")
            goal_study_time = st.number_input("目標学習時間（h/週）を入力してください。(例:8)",key="learning_time",step=1)
            exam_target_hours = list({item["target_hours"] for item in exam_data if item["exam_name"]==st.session_state["exam_name"]})[0]

            from services.unit_transform import total_to_week
            st.session_state["week_target_hours"] = total_to_week(exam_date,exam_target_hours)
            st.success(f"この資格に合格している人は週{st.session_state.week_target_hours}時間くらい勉強しています！")
            learning_materials = st.text_input("学習教材（参考書や問題集など）を入力してください", key="learning_materials")

            if exam_name and exam_date and goal_study_time:
                from services.db_operation import insert_data
                qualification_info = {
                    "user_id": session["user"]["id"],
                    "exam_id": st.session_state["exam_id"],
                    "exam_date": st.session_state["exam_date"],
                    "learning_materials": st.session_state["learning_materials"],
                    "learning_time":st.session_state["learning_time"]
                }

                register = st.button("資格情報を登録する", key="register_button",on_click=insert_data, args=("Learning materials", qualification_info))
                if register:
                    st.success("資格情報を登録しました！")

    with tabs[1]:
        from langchain_openai import ChatOpenAI
        from langchain.agents import create_agent
        from langgraph.checkpoint.memory import MemorySaver
        from llm.tools import confirm_exam, insert_db, check_exam_in_db,calc_goal_learning_time

        tools = [confirm_exam,check_exam_in_db,insert_db,calc_goal_learning_time]
        model = ChatOpenAI(model="gpt-4.1-nano", temperature=0.1,streaming=True)


        # Streamlitが再実行されても記憶が消えないように session_state に保存します
        if "memory" not in st.session_state:
            st.session_state.memory = MemorySaver()

        memory = st.session_state.memory
        prompt = """
            あなたは資格試験サポートのプロフェッショナルです。ユーザはどんな資格試験を受けるべきか迷っています。
            ユーザのニーズを聞き出し、資格試験の提案とデータベースの情報の確認や登録を行うエージェントです。
            # 依頼
            以下のSTEPに沿ってユーザのサポートをしてください。
            
            ## STEP1 受験する資格の提案・特定
            ニーズを聞き出してから、資格試験の提案をしてください。
            
            ## STEP2 試験日の確認・特定
            ユーザが資格名を伝えたら、confirm_examで資格名・受験日、CBT方式かどうかを取得し、
            受験日がある場合は受験日を伝え、CBT方式の場合はユーザに受験日を確認してください
            
            ## STEP3 週の目標勉強時間の提案・特定
            資格名と試験日の情報を集めたら、週の目標勉強時間をユーザに確認してください。確認する際に併せてcalc_goal_learning_timeで一般的な週の目標の勉強時間(h)をユーザに教えてください。
            
            ## STEP4 資格の登録
            資格名・試験日・週の目標勉強時間(h)の情報が集まったらconfirm_examツールを使い、ユーザに確認してください。
            ユーザが資格名と試験日を承認したら、insert_dbツールを使い、データベースに登録してください。
            """


        agent_executor = create_agent(model, tools,system_prompt=prompt ,checkpointer=memory)

        # スレッドIDの設定
        config = {"configurable": {"thread_id": "streamlit_user_id"}}

        # チャット履歴の表示
        snapshot = agent_executor.get_state(config)
        st.chat_message("assistant").markdown("こんにちは！資格試験に関する情報をお手伝いします。")
        if snapshot.values:
            for msg in snapshot.values["messages"]:
                # LangGraphのメッセージ形式をStreamlitに合わせて表示
                with st.chat_message(msg.type):
                    st.write(msg.content)

        # ユーザ入力とLLM実行
        if prompt := st.chat_input("でも聞いてください"):
            # ユーザーの入力を即時表示
            with st.chat_message("user"):
                st.write(prompt)

            # エージェントの実行と応答表示
            with st.chat_message("assistant"):
                # streamを使うと、文字が少しずつ出るような演出も可能です
                response_container = st.empty()
                full_response = ""

                # エージェントを実行 (入力は messages キーで渡す)
                # stream_mode="values" でメッセージの更新を受け取る
                events = agent_executor.stream(
                    {"messages": [("user", prompt)]},
                    config,
                    stream_mode="values"
                )

                for event in events:
                    # 最後のメッセージがAIからのものなら表示を更新
                    if "messages" in event:
                        last_msg = event["messages"][-1]
                        if last_msg.type == "ai":
                            full_response = last_msg.content
                            response_container.write(full_response)

# ------------ メイン画面 ------------
# ライブラリインポート

import datetime
from services.study_result import calc_consecutive,calc_weekly,calc_weekly_target
supabase = init_supabase()


# ------ 教材テーブルと資格テーブルから目標学習時間と残り日数を計算 ------
import pandas as pd

# --- 教材テーブルから目標学習時間と試験日(exam_date)を取得 ---
response = (supabase
            .table("Learning materials")
            .select("exam_id, learning_time, exam_date")
            .eq("user_id", st.session_state["user_id"])
            .single()
            .execute())
target_hours = int(response.data["learning_time"]) # 週間目標学習時間（時間）
exam_date_str = response.data["exam_date"]
# todo CBTかどうかで場合分け

# --- exam_dateが空欄だった場合の処理 ---
if exam_date_str is None:
    remaining_days_text = ""
else:
    exam_date = datetime.date.fromisoformat(exam_date_str) # exam_dateをstrからdate型に変換
    # 試験日までの日数計算
    today = datetime.date.today()
    remaining_days = exam_date - today
    remaining_days_text = f"{remaining_days.days} 日"

# ------ 勉強実績テーブルから連続日数を取得 ------
response = (supabase
            .table("Result")
            .select("date, time")
            .eq("user_id", st.session_state["user_id"] )
            .order("date", desc=False)
            .execute()
)
if len(response.data)>0:
    dates = [record["date"] for record in response.data]
    df = pd.DataFrame(response.data)
    df["date"] = pd.to_datetime(df["date"])
    df["time"] = pd.to_numeric(df["time"])

    # --- streamlitに表示 ---
    # 連続学習日数
    current_consecutive, max_consecutive = calc_consecutive(df["date"].tolist())
    current_consecutive_text = f"{current_consecutive}日"
    max_text = f"{max_consecutive}日"

    # 週間学習時間（実績）
    weekly_hours, weekly_minutes, delta_text = calc_weekly(df)
    weekly_text = f"{weekly_hours}時間 {weekly_minutes}分"
    weekly_progress = weekly_hours / target_hours * 100
    weekly_progress_text = f"{weekly_progress:.0f}%"

    # ------ ダッシュボード ------
    # st.subheader("📌勉強ダッシュボード")
    cards_container = st.container(horizontal=True)
    with cards_container:
        # 連続日数
        with st.container(height = 220, border=True):
            st.info("###### 🔥 連続学習日数")
            col1, col2 = st.columns(2, vertical_alignment="bottom")
            with col1:
                st.metric("", current_consecutive_text, delta=f"best: {max_text}")
            if max_consecutive == current_consecutive:
                with col2:
                    st.markdown(''':green[best更新中🎉]''')

        # 今週の学習時間
        with st.container(height = 220, border=True):
            st.info("###### 🖋 今週の学習時間")
            st.metric("", weekly_text, "進捗率: " + weekly_progress_text)

        # 試験日までの日数
        with st.container(height = 220, border=True):
            st.info("###### 📅 試験まであと")
            st.metric("", remaining_days_text, "")

        with st.container(height = 220, border=True):
            st.info("###### 💡 今の勉強時間は...")
            with st.container(horizontal=True):
                from services.show_image import show_image
                show_image(st.session_state["user_id"])
else:
    cards_container = st.container(horizontal=True)
    with cards_container:
        # 連続日数
        with st.container(height = 220, border=True):
            st.info("###### 🔥 連続学習日数")
            # col1, col2 = st.columns(2, vertical_alignment="bottom")
            # with col1:
            st.metric("", "0日", delta=f"best: 0日")

        # 今週の学習時間
        with st.container(height = 220, border=True):
            st.info("###### 🖋 今週の学習時間")
            st.metric("", "0時間", "前週比: ー")

        # 試験日までの日数
        with st.container(height = 220, border=True):
            st.info("###### 📅 試験まであと")
            st.metric("", remaining_days_text, "")

        with st.container(height = 220, border=True):
            st.info("###### 💡 今の勉強時間は...")
            with st.container(horizontal=True):
                from services.show_image import show_image
                show_image(st.session_state["user_id"])


# ---------- ここからタイマー機能 ----------
# ライブラリインポート
from services.timer import timer_start,timer_stop,timer_complete,timer_resume,format_time,timer_fragment,study_dialog
from PIL import Image
import time
# タイマー機能


# 初期化
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "running" not in st.session_state:
    st.session_state.running = False
if "accumulated_time" not in st.session_state:
    st.session_state.accumulated_time = 0  # 累積時間（トータル時間計算に利用）

sb = st.sidebar

sb.subheader("⏰勉強タイマー")

# gifファイルパス（動作中に使用）
gif_path = "assets/images/running.gif"
# 1フレーム目を取得（停止中に使用）
img = Image.open(gif_path)
first_frame = img.convert("RGBA") # gifを画像に変換

with st.sidebar:
    timer_fragment(st, gif_path, first_frame)

#==========================TODOを1つずつ表示================================
from services.show_todo import show_must_todo,todo_is_done,go_to_todo_register_page
from streamlit_product_card import product_card
st.subheader("今日のTODO")
is_todo = show_must_todo(st.session_state["user_id"]) # まだ終わっていないtodoがあるか判定

if is_todo:
    product_card(
        product_name=st.session_state["todo_title"],
        description=st.session_state["todo_content"],
        price=f"終了目標日：{st.session_state['todo_end_date']}",
        button_text="実施する",
        key="core_name_price_button",
        on_button_click=todo_is_done
    )
else:
    product_card(
        product_name="すばらしい！！今日のタスクは完了しました！",
        description="新しくタスクを追加したい場合は下のボタンをクリック！",
        button_text="TODOを登録する",
        key="todo_register_button",
        on_button_click=go_to_todo_register_page
    )

