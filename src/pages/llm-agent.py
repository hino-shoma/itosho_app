import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.messages import BaseMessage
from datetime import datetime,date
import asyncio
from services.submenu import submenu
from services.db_operation import google_login
from utility.applay_css import apply_custom_css
st.set_page_config(page_title="勉強コーチングAI",
                   layout="wide",
                   initial_sidebar_state="expanded",)
apply_custom_css("src/data/assets/css/style.css", "src/data/assets/images/background-image.png")


st.title("勉強コーチングAI")
session = google_login()
st.session_state["user_id"] = session["user"]["id"] 
submenu()

if "exam_name_agent" not in st.session_state:
    import json
    from services.db_operation import init_supabase,google_login
    supabase =init_supabase()

    # ユーザの資格登録情報を取得（あとでLLMのシステムプロンプトに入れるため）
    # TODO:資格が複数入ってくるDBの場合はデータの抽出条件の追加対応が必要
    exam_list = json.loads(supabase.table("Learning materials").select("*").eq("user_id",str(st.session_state.user_id)).execute().model_dump_json())
    if len(exam_list["data"])>0:
        exam_id = exam_list["data"][0]["exam_id"]
        exam =  json.loads(supabase.table("qualification").select("id,exam_name").eq("id",exam_id).execute().model_dump_json())
    else:
        exam={"data":[{}]}
        exam_list = {"data":[{}]}
    st.session_state["exam_name_agent"] = exam["data"][0].get("exam_name","情報なし")
    st.session_state["exam_date_agent"] = exam_list["data"][0].get("exam_date","情報なし")
    st.session_state["learning_materials_agent"] = exam_list["data"][0].get("learning_materials","情報なし")
    st.session_state["learning_time_agent"] = exam_list["data"][0].get("learning_time","情報なし")
    st.session_state["index_agent"] = exam_list["data"][0].get("index","情報なし")


# Streamlitが再実行されても記憶が消えないように session_state に保存します
if "memory_support" not in st.session_state:
    system_prompt = f"""
    あなたは資格試験サポートのプロフェッショナルです。
    
    # 依頼
    - ユーザのニーズや状況を聞き出し、以下の前提条件のユーザに最適な学習方法やスケジュールを提案してください。
    
    # 前提条件
    ユーザが受ける資格試験の情報は以下の通りです。

    資格名: {st.session_state.exam_name_agent}
    試験日: {st.session_state.exam_date_agent}
    学習教材: {st.session_state.learning_materials_agent}
    教材の目次:{st.session_state.index_agent}
    週の目標勉強時間:{st.session_state.learning_time_agent}時間

    
    
    # 注意点
    - ユーザは資格試験の勉強の仕方や何をすべきかを迷っています。
    - あなたはユーザの意図をくみ取って回答をする必要があります。
    - 会話の最初でユーザの情報が足りないときはまず提案をしてから追加で質問をして下さい。
    - 今日の日付は{datetime.now().date()}
    # 出力の形式
    - スケジュールを問われたときは日付、学習時間帯（10:00-11:00）、内容、TODOを表形式を提示してください
    
    
    """

@st.cache_resource
def get_llm():
    # LLMインスタンスをキャッシュすることで、再実行時のコストと遅延を削減できる。
    return ChatOpenAI(
        model="gpt-4.1-nano",
        temperature=0.1,
        streaming=True # ストリーミングあり
    )

HISTORY_KEY = "langchain_messages" 

def get_session_history(session_id: str) -> StreamlitChatMessageHistory:
    """
    RunnableWithMessageHistoryに渡すための関数。
    StreamlitChatMessageHistoryは内部でst.session_stateと同期できる
    """
    return StreamlitChatMessageHistory(key=HISTORY_KEY)


def setup_runnable_chain():
    llm = get_llm()
    
    # MessagesPlaceholderで履歴追加
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}")
    ])

    conversational_runnable = prompt | llm

    chain_with_history = RunnableWithMessageHistory(
        conversational_runnable,
        get_session_history, # 履歴オブジェクト
        input_messages_key="question", # ユーザー入力のキー
        history_messages_key="chat_history", # プロンプト内のプレースホルダーのキー
    )
    return chain_with_history

chain_with_history = setup_runnable_chain()

# StreamlitChatMessageHistoryインスタンスを取得
msgs = get_session_history(session_id="fixed_session_id") 

# st.fragmentを付けると、変更部分だけを更新してくれる
@st.fragment
def display_history(messages):
    if len(msgs.messages)==0:
        if st.session_state.index_agent =="情報なし":
            index = "なし" 
        else:
            index="あり"
        with st.chat_message("assistant"):
            if not st.session_state.exam_name_agent=="情報なし":
                st.markdown(f"""{st.session_state.exam_date_agent}の{st.session_state.exam_name_agent}のサポートをします！  
                            以下の登録情報を使いますね！  
                            **学習教材**： {st.session_state.learning_materials_agent}  
                            **教材の目次**：{index}  
                            **週の目標勉強時間**：{st.session_state.learning_time_agent}  """)
            else:
                st.write("資格勉強のサポートをしますね！")
    # 過去のメッセージをUIに再描画
    for msg in msgs.messages:
        if msg.type == "ai":
            role = "assistant"
        elif msg.type == "human":
            role = "user"
        else:
            role = "assistant" # あるいはエラー処理
        st.chat_message(role).markdown(msg.content)

display_history(msgs.messages)

async def async_stream_chain(prompt: str, chain) -> str:
    """
    非同期でチェーンを実行し、Streamlitのプレースホルダーを更新する
    """
    config = {"configurable": {"session_id": "fixed_session_id"}}
    full_response = ""
    placeholder = st.empty()
    
    # 実行メソッドを .stream から .astream に変更
    # ジェネレータが非同期になるため、async for を使用
    async for chunk in chain.astream({"question": prompt}, config=config):
        if chunk.content:
            full_response += chunk.content
            # リアルタイムで応答を更新し、カーソル(▌)を表示
            placeholder.markdown(full_response + "▌")
            
    # 応答完了後、カーソルを削除して最終応答を表示
    placeholder.markdown(full_response)
    
    # RWMHはストリーム後に自動で履歴を保存するため、ここで明示的な保存は不要
    return full_response


# ユーザー入力の受付
if prompt := st.chat_input("質問を入力してください"):
    # ユーザーメッセージを即座にUIに表示
    st.chat_message("user").markdown(prompt)
    
    # アシスタントの応答コンテナ
    with st.chat_message("assistant"):
        with st.spinner("ちょっと待ってくださいね。ただいま考え中です！"):
            
            # 2. 同期的なStreamlitの実行ブロック内で、非同期関数を同期的に実行
            #    これにより、LLMへのAPIコール中のI/O待ちが非同期で処理されます
            try:
                asyncio.run(async_stream_chain(prompt, chain_with_history))
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
