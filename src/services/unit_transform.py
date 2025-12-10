from datetime import datetime,date

def total_to_week(exam_date:date,target_total_hours:int)-> int:
    """
    資格試験の目標勉強時間と受験日から週当たりの目標勉強時間を算出する関数
    
    Args:
        exam_date:試験日
        target_total_hours:トータルの目標勉強時間(h)
    Returns:
        target_week_hours:試験日から逆算した週の目標勉強時間(h)
    """
    if isinstance(exam_date,str):
        tdatetime = datetime.strptime(exam_date, '%Y-%m-%d')
        exam_date = tdatetime.date()
    difference = exam_date - date.today()
    if difference.days>0:
        target_week_hours = int(target_total_hours/difference.days*7)
    else:
        target_week_hours = target_total_hours
    return  target_week_hours