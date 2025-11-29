import streamlit as st
import json
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from services.db_operation import init_supabase

# TODO:セッション情報をもとに資格の情報を検索しているため、メイン画面に一度行かないと正しく情報の紐づけができない
supabase =init_supabase()
try:
    exam_list = json.loads(supabase.table("Learning materials").select("user_id,exam_id,exam_date,learning_materials").eq("user_id",str(st.session_state.user_id)).execute().model_dump_json())
    exam_id = exam_list["data"][0]["exam_id"]
    exam =  json.loads(supabase.table("qualification").select("id,exam_name").eq("id",exam_id).execute().model_dump_json())
    st.session_state["exam_name_agent"] = exam["data"][0]["exam_name"]
    st.session_state["exam_date_agent"] = exam_list["data"][0]["exam_date"]
    st.session_state["learning_materials_agent"] = exam_list["data"][0]["learning_materials"]
    st.session_state["learning_time_agent"] = exam_list["data"][0]["learning_time"]
except:
    st.session_state["exam_name_agent"] = "情報登録なし"
    st.session_state["exam_date_agent"] = "情報登録なし"
    st.session_state["learning_materials_agent"] = "情報登録なし"
    st.write("登録情報なし")


model = ChatOpenAI(model="gpt-5-nano", temperature=0)

# Streamlitが再実行されても記憶が消えないように session_state に保存します
if "memory_support" not in st.session_state:
    st.session_state.memory_support = MemorySaver()

memory = st.session_state.memory_support
prompt = f"""
    あなたは資格試験サポートのプロフェッショナルです。ユーザは資格試験の勉強の仕方や何をすべきかを迷っています。
    ユーザのニーズや状況を聞き出し、アサーティブにユーザの意図に沿った回答を心がけてください。

    ユーザが受ける資格試験の情報は以下の通りです。

    資格名: {st.session_state.exam_name_agent}
    試験日: {st.session_state.exam_date_agent}
    学習教材: {st.session_state.learning_materials_agent}

    これらの情報を元に、ユーザに最適な学習方法やスケジュールを提案してください。
    """


agent_executor = create_agent(model,system_prompt=prompt ,checkpointer=memory)

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