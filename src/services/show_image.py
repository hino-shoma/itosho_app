
import streamlit as st
from services.db_operation import fetch_data
import pandas as pd

def show_image(user_id):
    """
    勉強時間に応じて頑張った感のある画像を出力する
    Args:
        user_id:ログイン中のユーザID
    """
    select_col_list = ["*"]
    image_data = fetch_data("images", select_col_list)
    result = fetch_data("Result", select_col_list)
    _df_result = pd.DataFrame(result)
    df_result = _df_result[_df_result["user_id"]==user_id]
    df_image = pd.DataFrame(image_data)
    total_hour = int(df_result["time"].astype(int).sum()/60/60)
    view_hours_list = [hours["view_hours"] for hours in image_data]
    selected = max([v for v in view_hours_list if v <= total_hour], default=None)
    df_filter = df_image[df_image["view_hours"]==selected]

    # TODO:同じ時間に複数画像があると同じ内容しか表示されない
    content = df_filter["content"].iloc[-1]
    url = df_filter["image_url"].iloc[-1]
    col1,col2 = st.columns(2)
    with col1:
        st.write(content)
    with col2:
        st.image(
            url,
            width="stretch"
        )