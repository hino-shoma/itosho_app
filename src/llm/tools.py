import streamlit as st
from langchain.tools import tool, ToolRuntime
from datetime import date
from llm.models import ExamInfo
from services.db_operation import fetch_data,insert_data



@tool(description="資格名を受け取り、データベースの情報と照合するツール")
def check_exam_in_db(exam_name:str) -> None:
    """資格名を受け取り、データベースの情報と照合するツール"""
    select_col_list = ["exam_name"]
    exam_data = fetch_data("qualification", select_col_list)
    exam_names_in_db = [item["exam_name"] for item in exam_data]

    if exam_name in exam_names_in_db:
        with st.chat_message("assistant"):
            st.write(f"「{exam_name}」はデータベースに存在します。")
    else:
        with st.chat_message("assistant"):
            st.write(f"""申し訳ございませんが、{exam_name}」はデータベースに存在しません。
                登録されている資格名は以下の通りです。
                {', '.join(exam_names_in_db)}
                新しい資格名を登録したい場合は、管理者にお問い合わせください。""")

@tool(args_schema=ExamInfo,description="資格名と試験日の入力がされたらこのツールを使い、情報を確認する")
def confirm_exam(exam_name:str, exam_date:date) -> None:
    """資格名と試験日を受け取り、情報を確認するツール"""
    with st.chat_message("assistant"):
            st.write(f"""この試験を受けますか？
            試験名: {exam_name}
            試験日: {exam_date}
            はい/いいえで答えてください。""")


@tool(args_schema=ExamInfo,description="ユーザが受けたい資格名・試験日が分かったら、必ず利用するツール")
def insert_db(exam_name:str, exam_date:date,runtime: ToolRuntime[ExamInfo]) -> None:
    """資格名・試験日が分かったら必ず使用するツールで、データベースに登録する"""

    data = {"user_id":st.session_state['user_id'],"exam_name": exam_name,"exam_date": exam_date}
    insert_data("Learning materials", data)
    with st.chat_message("assistant"):
            st.write(f"データベースに登録しました！")

