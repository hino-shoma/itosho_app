import streamlit as st
from langchain.tools import tool, ToolRuntime
from datetime import date
from llm.models import ExamInfo
from services.db_operation import fetch_data,insert_data,update_data

# グローバル変数としてuser_idを保持
_user_id = None

def set_user_id(user_id: str):
    """ツールで使用するuser_idを設定"""
    global _user_id
    _user_id = user_id

def _get_user_id():
    """user_idを取得"""
    global _user_id
    if _user_id is None:
        # フォールバック: session_stateから取得
        return st.session_state.get('user_id', None)
    return _user_id

@tool(description="資格名からデータベースの情報と照合するツール。CBT方式だったらユーザに日付を確認")
def check_exam_in_db(exam_name:str) -> str:
    """資格名を受け取り、データベースの情報と照合するツール"""
    select_col_list = ["exam_name","is_CBT","exam_date"]
    exam_data = fetch_data("qualification", select_col_list)
    exam_names_in_db = [item["exam_name"] for item in exam_data]
    is_CBT = list({item["is_CBT"] for item in exam_data if item["exam_name"]==exam_name})[0]
    
    if exam_name in exam_names_in_db:
        return f"「{exam_name}」はデータベースに存在します。CBT方式か:{is_CBT}。TrueだったらCBT方式なので日付をユーザに確認"
    else:
        return f"""申し訳ございませんが、{exam_name}」はデータベースに存在しません。
                登録されている資格名は以下の通りです。
                {', '.join(exam_names_in_db)}
                新しい資格名を登録したい場合は、管理者にお問い合わせください。"""

@tool(description="資格名からデータベースの情報と照合するツール。CBT方式だったらユーザに日付を確認")
def calc_goal_learning_time(exam_name:str,exam_date:date)-> str:
    """
    資格試験名と受験日から週当たりの目標勉強時間を算出する関数
    
    Args:
        exam_date:試験日
        target_total_hours:トータルの目標勉強時間(h)
    Returns:
        target_week_hours:試験日から逆算した週の目標勉強時間(h)
    """
    from datetime import datetime,date
    select_col_list = ["exam_name","target_hours"]
    exam_data = fetch_data("qualification", select_col_list)
    target_total_hours = list({item["target_hours"] for item in exam_data if item["exam_name"]==exam_name})[0]
    if isinstance(exam_date,str):
        tdatetime = datetime.strptime(exam_date, '%Y-%m-%d')
        exam_date = tdatetime.date()
    difference = exam_date - date.today()
    if difference.days>0:
        target_week_hours = int(target_total_hours/difference.days*7)
    else:
        target_week_hours = 0
    return  f"今日の日付：{date.today()},試験日までの日数：{difference.days},目標トータル勉強時間：{target_total_hours}なので、この資格を受ける人の週の勉強時間の目安は{target_week_hours}時間/週であることを伝えてください。"


@tool(args_schema=ExamInfo,description="資格名と試験日、週の目標勉強時間の入力がされたらこのツールを使い、情報を確認する")
def confirm_exam(exam_name:str, exam_date:date,learning_time:int) -> None:
    """資格名と試験日を受け取り、情報を確認するツール"""
    return f"""この試験を受けますか？
            試験名: {exam_name}
            試験日: {exam_date}
            週の目標勉強時間: {learning_time}
            はい/いいえで答えてください。"""

@tool(args_schema=ExamInfo,description="ユーザが受けたい資格名・試験日・週の目標勉強時間が分かったら、必ず利用するツール")
def insert_db(exam_name:str, exam_date:date,learning_time:int) -> str:
    """資格名・試験日・週の目標勉強時間が分かったら必ず使用するツールで、データベースに登録する"""
    # user_idはグローバル変数から取得
    select_col_list = ["exam_name","id"]
    exam_data = fetch_data("qualification", select_col_list)
    exam_id = list({item["id"] for item in exam_data if item["exam_name"]==exam_name})[0]

    user_id = _get_user_id()
    data = {"user_id": user_id, "exam_id": exam_id, "exam_date": exam_date, "learning_time": learning_time}
    insert_data("Learning materials", data)
    return f"データベースに登録しました！"

@tool(args_schema=ExamInfo,description="ユーザが受けたい資格名・試験日・週の目標勉強時間が分かったら、必ず利用するツール")
def update_db(exam_name:str, exam_date:date,learning_time:int) -> str:
    """資格名・試験日・週の目標勉強時間が分かったら必ず使用するツールで、データベースを更新する"""
    # user_idはグローバル変数から取得
    select_col_list = ["exam_name","id"]
    exam_data = fetch_data("qualification", select_col_list)
    exam_id = list({item["id"] for item in exam_data if item["exam_name"]==exam_name})[0]

    user_id = _get_user_id()
    data = {"user_id": user_id, "exam_id": exam_id, "exam_date": exam_date, "learning_time": learning_time}
    update_data("Learning materials", data,user_id)
    return f"データベースを更新登録しました！"

