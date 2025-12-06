def submenu():
    import streamlit as st
    sb = st.sidebar
    sb.header("メニュー")
    sb.page_link("main.py", label="メイン", icon="📌")
    sb.page_link("pages/llm-agent.py", label="ToDo一覧", icon="✅") # todo todoページができたらリンクを変更
    sb.page_link("pages/llm-agent.py", label="資格の確認・変更", icon="📓") # todo todoページができたらリンクを変更
    sb.page_link("pages/llm-agent.py", label="お悩み相談", icon="🧑‍🏫")

    # --- ページナビゲーションを非表示にするCSS ---
    hide_streamlit_style = """
        <style>
            /* デフォルトのページ切り替えナビを非表示 */
            [data-testid="stSidebarNav"] {
                display: none !important;
            }
            /* ヘッダーに出るページタイトルも消したい場合 */
            header[data-testid="stHeader"] {
                display: none !important;
            }
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)