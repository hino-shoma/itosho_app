from services.db_operation import init_supabase,google_login
import pandas as pd
import json
from utility.applay_css import apply_custom_css
from services.submenu import submenu
import streamlit as st
st.set_page_config(
    page_title="登録情報の確認・変更",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_custom_css("src/data/assets/css/style.css")



# if "user_id" not in st.session_state:
session = google_login()
st.session_state["user_id"] = session["user"]["id"] 
submenu()
supabase = init_supabase()

# TODO:資格が複数入ってくるDBの場合はデータの抽出条件の追加対応が必要
exam_list = json.loads(supabase.table("Learning materials").select("*").eq("user_id",str(st.session_state.user_id)).execute().model_dump_json())
exam_id = exam_list["data"][0]["exam_id"]
exam =  json.loads(supabase.table("qualification").select("id,exam_name").eq("id",exam_id).execute().model_dump_json())
st.session_state["exam_name_setting"] = exam["data"][0].get("exam_name","情報なし")
st.session_state["exam_date_setting"] = exam_list["data"][0].get("exam_date","情報なし")
st.session_state["learning_materials_setting"] = exam_list["data"][0].get("learning_materials","情報なし")
st.session_state["learning_time_setting"] = exam_list["data"][0].get("learning_time","情報なし")
st.session_state["index_setting"] = exam_list["data"][0].get("index","情報なし")

    # 情報を集約
data = {
    '項目': [
        '試験名', 
        '受験日', 
        '学習教材', 
        '週の学習時間', 
        'インデックス'
    ],
    '登録情報': [
        st.session_state.get("exam_name_setting", "情報なし"),
        st.session_state.get("exam_date_setting", "情報なし"),
        st.session_state.get("learning_materials_setting", "情報なし"),
        st.session_state.get("learning_time_setting", "情報なし"),
        st.session_state.get("index_setting", "情報なし")
    ]
}
df = pd.DataFrame(data)

st.subheader("資格情報の確認・変更")
st.dataframe(df,width="stretch",hide_index=True)


st.space("medium")
tabs = st.tabs(["登録情報の修正", "どんな資格があるか相談したい"])


from services.db_operation import fetch_data
select_col_list = ["id","exam_category","exam_name", "exam_date","is_CBT","target_hours"]
exam_data = fetch_data("qualification", select_col_list)
category = list({item["exam_category"] for item in exam_data})

with tabs[0]:
    st.markdown(f"")
    
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
        learning_materials_index = st.text_input("学習教材（参考書や問題集など）の目次を入力してください", key="learning_materials_index")

        if exam_name and exam_date and goal_study_time:
            from services.db_operation import update_data
            qualification_info = {
                "user_id": session["user"]["id"],
                "exam_id": st.session_state["exam_id"],
                "exam_date": st.session_state["exam_date"],
                "learning_materials": st.session_state["learning_materials"],
                "index": st.session_state["learning_materials_index"],
                "learning_time":st.session_state["learning_time"]
            }

            register = st.button("資格情報を更新する", key="register_button",on_click=update_data, args=("Learning materials", qualification_info))
            if register:
                st.success("資格情報を更新しました！")

with tabs[1]:
    from langchain_openai import ChatOpenAI
    from langchain.agents import create_agent
    from langgraph.checkpoint.memory import MemorySaver
    from llm.tools import confirm_exam, insert_db, check_exam_in_db

    tools = [confirm_exam,check_exam_in_db,insert_db]
    model = ChatOpenAI(model="gpt-4.1-nano", temperature=0)


    # Streamlitが再実行されても記憶が消えないように session_state に保存します
    if "memory" not in st.session_state:
        st.session_state.memory = MemorySaver()

    memory = st.session_state.memory
    prompt = """
        あなたは資格試験サポートのプロフェッショナルです。ユーザはどんな資格試験を受けるべきか迷っています。
        ユーザのニーズを聞き出し、資格試験の提案とデータベースの情報の確認や登録を行うエージェントです。
        まず、ニーズを聞き出してから、資格試験の提案をしてください。
        ユーザが資格名のみを伝えたら、check_exam_in_dbツールを使い、データベースにその資格名が存在するか確認してください。
        ユーザが資格名と試験日を伝えたら、confirm_examツールを使い、ユーザに確認してください。
        ユーザが資格名と試験日を承認したら、insert_dbツールを使い、データベースに登録してください。
        """


    agent_executor = create_agent(model, tools,system_prompt=prompt ,checkpointer=memory)

    # スレッドIDの設定
    config = {"configurable": {"thread_id": "streamlit_user_id"}}

    # チャット履歴の表示
    snapshot = agent_executor.get_state(config)
    st.chat_message("assistant").markdown("こんにちは！どんな資格をお探しですか？")
    if snapshot.values:
        for msg in snapshot.values["messages"]:
            # LangGraphのメッセージ形式をStreamlitに合わせて表示
            with st.chat_message(msg.type):
                st.write(msg.content)

    # ユーザ入力とLLM実行
    if prompt := st.chat_input("何でも聞いてください"):
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
