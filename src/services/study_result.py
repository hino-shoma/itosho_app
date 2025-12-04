import pandas as pd
# --- 連続学習日数を計算 ---
def calc_consecutive(dates):
    if len(dates) == 0:
        return 0, 0
    
    dates = sorted(list(set(dates)))  # 重複削除とソート
    
    consecutive = 1
    max_consecutive = 1
    current_consecutive = 1
    
    for i in range(1, len(dates)):
        if (dates[i] - dates[i-1]).days == 1:
            consecutive += 1
        else:
            consecutive = 1
        max_consecutive = max(max_consecutive, consecutive)
    
    # 直近が昨日・今日で途切れていないか確認
    today = pd.Timestamp("today").normalize()
    
    if dates[-1] == today:
        current_consecutive =  consecutive
    elif dates[-1] == today - pd.Timedelta(days=1):
        current_consecutive = consecutive
    else:
        current_consecutive = 0
    
    return current_consecutive, max_consecutive

# ------ 勉強実績テーブルから週間学習時間を取得 ------
def calc_weekly(df):
    today = pd.Timestamp.today().normalize()
    # 今週の学習時間
    monday = today - pd.Timedelta(days = today.weekday()) # 月曜日の日付を計算
    df_this_week = df[df["date"].between(monday, today)] # 月曜～今日まで
    this_week_seconds = df_this_week["time"].sum()
    # 先週の学習時間
    last_monday = monday - pd.Timedelta(days = 7)
    last_sunday = monday - pd.Timedelta(days = 1)
    df_last_week = df[df["date"].between(last_monday, last_sunday)]
    last_week_seconds = df_last_week["time"].sum()
    
    # 時間と分に換算（今週のみ）
    hours = this_week_seconds // 3600
    minutes = (this_week_seconds % 3600) // 60
    
    # 先週との比較
    if last_week_seconds == 0:
        delta_percent = 100 # 先週ゼロの時：100%と表示
        delta_text = f"+{delta_percent}%"
    else:
        delta_percent = round((this_week_seconds / last_week_seconds) * 100)
        delta_text = f"{delta_percent}%"
        
    return hours, minutes, delta_text

# ------ 資格テーブルから残り日数を取得 ------
# --- 週間の目標学習時間を計算（total_time & exam_date より）---
def calc_weekly_target(target_hours, exam_date):
    today = pd.Timestamp.today().normalize()

    # 残り日数
    remaining_days = (exam_date - today).days
    if remaining_days <= 0:
        remaining_days = 1  # 過ぎていてもエラー防止

    # 1日あたりの目標学習時間（秒）
    daily_target_seconds = int(target_hours) * 3600 / remaining_days

    # 今週の経過日数（月曜〜今日）
    monday = today - pd.Timedelta(days=today.weekday())
    days_this_week = (today - monday).days + 1

    # 今週の目標時間（秒）
    weekly_target_seconds = daily_target_seconds * days_this_week

    # 時間＋分へ変換
    hours = int(weekly_target_seconds // 3600)
    minutes = int((weekly_target_seconds % 3600) // 60)

    return hours, minutes