import streamlit as st
import json
from supabase import create_client, Client
from datetime import datetime, date
from streamlit_supabase_auth import login_form, logout_button


# 環境変数（secrets.toml）から設定を取得
REDIRECT_URL = st.secrets["redirect_uri"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def init_supabase():
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase




def google_login():
    session = login_form(
        url=SUPABASE_URL,
        apiKey=SUPABASE_KEY,
        providers=["google"],
    )
    if not session:
        st.stop()

    # Update query param to reset url fragments
    st.query_params.clear()

    with st.sidebar:
        st.write(f"ようこそ！ {session['user']['user_metadata']['full_name']}さん")
        # st.write(session)
        logout_button()
    return session

def fetch_data(table_name: str, select_col_list: list[str])-> list[dict]:
    """
    指定したテーブルからデータを取得する関数
    Args:
        table_name (str): 取得するテーブル名
        select_col_list (list[str]): 取得するカラム名のリスト
    Returns:
        list[dict]: 取得したデータのリスト
    """
    select_col_str = ",".join(select_col_list)
    data = supabase.table(table_name).select(select_col_str).execute()
    data=data.model_dump_json()
    data = json.loads(data)
    return data["data"]

def insert_data(table_name: str, insert_data: dict)-> None:
    """
    指定したテーブルにデータを挿入する関数
    Args:
        table_name (str): 挿入するテーブル名
        insert_data (dict): 挿入するデータ{列名：値, ...}
    Returns: None
    """
    def json_serial(obj):
        """
        JSONシリアライズ可能な形式に変換するヘルパー関数
        Args:
            obj: シリアライズ可能な形式に変換するオブジェクト
        Returns: シリアライズ可能な形式のオブジェクト"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError (f'Type {obj} not serializable')
    
    insert_data = json.loads(json.dumps(insert_data, default=json_serial))
    supabase.table(table_name).insert(insert_data).execute()

def update_data(table_name: str, insert_data: dict,user_id)-> None:
    """
    指定したテーブルにデータを挿入する関数
    Args:
        table_name (str): 挿入するテーブル名
        insert_data (dict): 挿入するデータ{列名：値, ...}
        user_id:ユーザのUID
    Returns: None
    """
    def json_serial(obj):
        """
        JSONシリアライズ可能な形式に変換するヘルパー関数
        Args:
            obj: シリアライズ可能な形式に変換するオブジェクト
        Returns: シリアライズ可能な形式のオブジェクト"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError (f'Type {obj} not serializable')
    
    insert_data = json.loads(json.dumps(insert_data, default=json_serial))
    supabase.table(table_name).update(insert_data).eq("user_id",user_id).execute()

