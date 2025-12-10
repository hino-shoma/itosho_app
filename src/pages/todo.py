import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
import datetime
from services.db_operation import google_login
from utility.applay_css import apply_custom_css
from services.submenu import submenu
# ============== ログイン処理=============================
session = google_login()
st.session_state["user_id"] = session["user"]["id"] # セッションにuser_idを入れる
apply_custom_css("src/data/assets/css/style.css", "src/data/assets/images/background-image.png")
submenu()
# Supabase接続
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("ToDoリスト")
st.write("<span style='color:red'>終了日が近い＆優先度の高いものから上から順番に表示しています</span>", unsafe_allow_html=True)

def load_data():
    response = supabase.table("todolist").select("id,priority,category,title,content,start_date,end_date,done,delete,done_status").eq("user_id", st.session_state["user_id"]).execute()
    return pd.DataFrame(response.data)

#Learning_materialsテーブルから情報を習得する
def load_Learning_materials():
    response = supabase.table("Learning materials").select("exam_date").eq("user_id", st.session_state["user_id"]).execute()
    return pd.DataFrame(response.data)

df = load_data()
print(df)
#文字列をそれぞれの型に変換する。
df["id"] = df["id"].astype("Int8")
df["start_date"] = pd.to_datetime(df["start_date"]).dt.date
df["end_date"]   = pd.to_datetime(df["end_date"]).dt.date

#表の大きさを大きくする
st.set_page_config(layout="wide")

# 優先度を順序付きカテゴリに変換
df["priority"] = pd.Categorical(
    df["priority"],
    categories=["高", "中", "低"],  # 並び順を定義
    ordered=True
)

# 優先度（高→低）＋ 完了フラグ（False→True）でソート
sorted_df = df.sort_values(by=["done","end_date","priority"], ascending=[True, True, True])

# Indexを削除（ソートするとIndexが再度画面に表示されてしまうため、indexを削除する）
sorted_df = sorted_df.reset_index(drop=True)

if 'discount' not in st.session_state:
    st.session_state.discount = 10



#表の表示をする
edited = st.data_editor(
    sorted_df.drop(columns=["id","done_status"]),
    num_rows = "dynamic",
    column_config={
        "category": st.column_config.SelectboxColumn("カテゴリ", options=["セキュリティ","ネットワーク","プログラミング","経営戦略","ソフトウェア","ハードウェア"]),
        "priority": st.column_config.SelectboxColumn("優先度", options=["高","中","低"]),
        "title": st.column_config.TextColumn("タイトル"),
        "content": st.column_config.TextColumn("内容", width="large"),
        "start_date": st.column_config.DateColumn("開始日", format="YYYY-MM-DD"),
        "end_date": st.column_config.DateColumn("終了日", format="YYYY-MM-DD"),
        "done": st.column_config.CheckboxColumn("完了"),
        "delete": st.column_config.CheckboxColumn("削除"),        
    },
    width="stretch"
)

if st.button("保存"):
    # id を戻して結合する。
    df_updated = pd.concat([sorted_df[["id"]], edited], axis=1)
    
    # 日付を文字列に変換
    df_updated["start_date"] = pd.to_datetime(df_updated["start_date"]).dt.strftime("%Y-%m-%d")
    df_updated["end_date"]   = pd.to_datetime(df_updated["end_date"]).dt.strftime("%Y-%m-%d")

    for _, row in df_updated.iterrows():
        if pd.notna(row["id"]):
            # --- UPDATE ---
            supabase.table("todolist").update({
                "category": row["category"],
                "priority": row["priority"],
                "title": row["title"],
                "content": row["content"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "done": bool(row["done"]),
                "delete": bool(row["delete"])
            }).eq("id", row["id"]).execute()
        else:
            # --- INSERT ---
            supabase.table("todolist").insert({
                "category": row["category"],
                "user_id": st.session_state["user_id"],
                "priority": row["priority"],
                "title": row["title"],
                "content": row["content"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "done": bool(row["done"]),
                "delete": bool(row["delete"])
            }).execute()
    st.rerun()
    
if st.button("削除欄にチェックをしたものを全て消去する"):
    df_updated = pd.concat([df[["id"]], edited], axis=1)
    for _, row in df_updated.iterrows():
        if row["delete"] == True:
            supabase.table("todolist").delete().eq("id",int(row["id"])).execute()
    st.rerun()


import streamlit as st
import pandas as pd
import plotly.express as px
st.title("ToDoの進捗状況")



# ガントチャート用のサンプルデータを作成


# 日付型に変換
sorted_df["start_date"] = pd.to_datetime(sorted_df["start_date"])
sorted_df["end_date"] = pd.to_datetime(sorted_df["end_date"])

# 今日の日付（Streamlit実行時の日付）を取得
today = pd.to_datetime("today").normalize()

# 終了日が今日の日付よりも前の場合赤色で表示させる。
# 完了している場合は緑色にする。
# 進行中の場合は青色にする。

def status(row):
    if row["end_date"] < today and row["done"] != 1:
        return "期限切れ"   # 赤
    elif row["done"] == 1:
        return "完了済"     # 緑
    else:
        return "進行中"     # 青

sorted_df["done_status"] = sorted_df.apply(status, axis=1)

# ガントチャート作成
fig = px.timeline(
    sorted_df,
    x_start="start_date",
    x_end="end_date",
    y="title",
    hover_data="content",
    color="done_status",  # ステータスごとに色分け
    color_discrete_map={
        "完了済": "green",   # 完了済 → 緑
        "進行中": "blue",    # 進行中 → 青
        "期限切れ": "red"    # 期限切れ → 赤
    },
    labels={"content": "内容","start_date":"開始日","end_date":"終了日","title":"タスク名","done_status":"進捗状況"}
)

# 軸ラベルを変更
fig.update_layout(
    xaxis_title="開始日〜終了日",   # X軸ラベル
    yaxis_title="タスク名",       # Y軸ラベル
    legend_title_text="進捗状況"
)


# 今日の日付に縦線を追加
fig.add_shape(
    type="line",
    x0=today, x1=today,   # X軸方向に固定（今日の日付）
    y0=0, y1=1,           # グラフ全体に線を引く
    xref="x", yref="paper",
    line=dict(color="black", width=3, dash="solid")
)

# 「今日」という文言を加える。
fig.add_annotation(
    x=today,              # 今日の日付の位置
    y=1,                  # X軸上に配置（y=0）
    xref="x", yref="paper",
    text= f"本日 {today.strftime('%m/%d')}",          # 注釈テキスト
    showarrow=False,
    font=dict(color="black", size=20),
    align="center",
    yanchor="bottom"         # X軸のすぐ下に配置
)

#examにデータを抽出、DATE型に変換
exam = load_Learning_materials()
exam["exam_date"] = pd.to_datetime(exam["exam_date"])
exam_date = exam["exam_date"].iloc[0]

fig.add_shape(
    type="line",
    x0=exam_date, x1=exam_date,
    y0=0, y1=1,
    xref="x", yref="paper",
    line=dict(color="red", width=3, dash="solid")
)

fig.add_annotation(
    x=exam_date,
    y=1,
    xref="x", yref="paper",
    text= f"試験日 {exam_date.strftime('%m/%d')}",
    showarrow=False,
    font=dict(color="red", size=20),
    align="center",
    yanchor="bottom"
)

# 横軸の表示形式を MM/DD 表記に変更、1日ごとに表示する
fig.update_xaxes(
    tickformat="%m/%d",   # MM/DD 表記
    showgrid=True,        # グリッド線を表示
    gridcolor="lightgray" # グリッド線の色
)

# Y軸のタスク順序を反転（下から順に表示） ※任意
fig.update_yaxes(
    autorange="reversed",
)

fig.update_traces(width=0.4)

# Streamlitでチャートを表示
st.plotly_chart(fig, use_container_width=True)