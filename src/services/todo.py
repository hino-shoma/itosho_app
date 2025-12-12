from datetime import date
from services.db_operation import insert_data
import time
import streamlit as st

def first_insert_todo():
    today = date.today().isoformat()
    data = {"user_id": st.session_state.user_id,"priority":"高", "start_date": today, "end_date": today,"title":"受ける資格を決める！","content":"アプリ上で資格を登録する","done":True}
    insert_data("todolist", data)
    time.sleep(2)