from services.db_operation import init_supabase
import json
import pandas as pd
import streamlit as st
supabase = init_supabase()

def show_must_todo(user_id):
    try:
        _todo = supabase.table("todolist").select("*").eq("user_id", user_id).neq("done",True).execute()

        todo_list = _todo.model_dump_json()

        df = pd.DataFrame(json.loads(todo_list)["data"])
        min_end_date=df["end_date"].min()
        todo =df[df["end_date"]==min_end_date]

        st.session_state["todo_title"]=todo["title"].iloc[-1]
        st.session_state["todo_content"] = todo["content"].iloc[-1]
        st.session_state["todo_end_date"] = todo["end_date"].iloc[-1]
        st.session_state["todo_id"] = todo["id"].iloc[-1]
        st.session_state["is_not_done_todo"] = True
    except:
        st.session_state["is_not_done_todo"] = False
    return st.session_state["is_not_done_todo"]

@st.dialog("TODOを完了させますか？")
def todo_is_done():
    st.write(f"タスク名：{st.session_state.todo_title}")
    st.write(f"内容：{st.session_state.todo_content}")
    st.write(f"終了目標日：{st.session_state.todo_end_date}")
    finish_todo_time = st.number_input("かかった勉強時間(分)",step=1)
    
    if st.button("完了",type="primary"):
        from services.timer import save_study_record
        import time
        supabase.table("todolist").update({"done":True}).eq("id",st.session_state.todo_id).execute()
        save_study_record(st.session_state["user_id"],finish_todo_time*60)
        st.balloons()
        time.sleep(2)
        st.rerun()
        
def go_to_todo_register_page():
    st.switch_page("pages/llm-agent.py")