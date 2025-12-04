from services.db_operation import init_supabase
import json
import pandas as pd
import streamlit as st

def show_must_todo(user_id):
    supabase = init_supabase()
    _todo = supabase.table("todo").select("*").eq("user_id", user_id).eq("done",False).execute()

    todo_list = _todo.model_dump_json()

    df = pd.DataFrame(json.loads(todo_list)["data"])
    min_end_date=df["end_date"].min()
    todo =df[df["end_date"]==min_end_date]

    st.session_state["todo_title"]=todo["title"].iloc[-1]
    st.session_state["todo_content"] = todo["content"].iloc[-1]
    st.session_state["todo_end_date"] = todo["end_date"].iloc[-1]