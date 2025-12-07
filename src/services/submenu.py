def submenu():
    import streamlit as st
    sb = st.sidebar
    sb.header("メニュー")
    sb.page_link("main.py", label="メイン", icon="📌")
    sb.page_link("pages/todo.py", label="ToDo一覧", icon="✅") # todo todoページができたらリンクを変更
    sb.page_link("pages/setting.py", label="資格の確認・変更", icon="📓") # todo todoページができたらリンクを変更
    sb.page_link("pages/llm-agent.py", label="お悩み相談", icon="🧑‍🏫")