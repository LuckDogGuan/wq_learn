import os
import logging
import time
import requests
import datetime  # 新增导入
from machine_lib import *

s = sess = login()


def wait_get(url: str, max_retries: int = 10) -> "Response":
    retries = 0
    while retries < max_retries:
        while True:
            simulation_progress = sess.get(url)
            if simulation_progress.headers.get("Retry-After", 0) == 0:
                break
            time.sleep(float(simulation_progress.headers["Retry-After"]))
        if simulation_progress.status_code < 400:
            break
        else:
            time.sleep(2 ** retries)
            retries += 1
    return simulation_progress

def check_consecutive_non_zero_values(alpha_id, data, required_streak=200):
    if not data or len(data) < required_streak:
        return True

    def check_column(column_data):
        if len(column_data) < required_streak:
            return True

        current_streak_count = 0
        current_streak_value = None

        for value in column_data:
            if value != 0:
                if value == current_streak_value:
                    current_streak_count += 1
                else:
                    current_streak_value = value
                    current_streak_count = 1
            else:
                current_streak_value = None
                current_streak_count = 0

            if current_streak_count >= required_streak:
                return False
        return True

    column1_values = []
    column2_values = []
    for row in data:
        if len(row) >= 3:
            column1_values.append(row[1])
            column2_values.append(row[2])
        else:
            pass
    if column1_values and column2_values:
        is_col1_all_zeros = all(v == 0 for v in column1_values)
        is_col2_all_zeros = all(v == 0 for v in column2_values)
        if is_col1_all_zeros or is_col2_all_zeros:
            print(alpha_id, "不合法")
            return False
    if not check_column(column1_values):
        print(alpha_id, "不合法")
        return False

    if not check_column(column2_values):
        print(alpha_id, "不合法")
        return False
    #print(alpha_id, "通过")
    return True

import datetime

def get_alpha_pnl_legal(alpha_id: str) -> bool:
    not_legal_id=[]
    pnl = wait_get("https://api.worldquantbrain.com/alphas/" + alpha_id + "/recordsets/pnl").json()
    records = pnl["records"]
   
    # 1. 检查时间跨度是否≥8年
    if not records:
        return False
       
    date_list = []
    for record in records:
        try:
            date_obj = datetime.datetime.strptime(record[0], '%Y-%m-%d').date()
            date_list.append(date_obj)
        except Exception:
            return False  # 日期格式错误
           
    min_date = min(date_list)
    max_date = max(date_list)
    total_days = (max_date - min_date).days
    if total_days < 2920:  # 2920天 ≈ 8年
        return False
   
    # 2. 检查是否连续多年零值（重点关注前两列PNL）
    zero_streak_threshold = 5 * 252  # 假设每年252个交易日
    col1_zeros = [record[1] == 0 for record in records]  # Combo PnL列或RA PNL列
    #SA需要取消下面的注释
    #col2_zeros = [record[2] == 0 for record in records]  # Equal Weight PnL列
   
    # 检测连续零值的最大长度
    def max_consecutive_zeros(arr):
        max_streak = current_streak = 0
        for val in arr:
            current_streak = current_streak + 1 if val else 0
            max_streak = max(max_streak, current_streak)
        return max_streak
   
    col1_max_zero_streak = max_consecutive_zeros(col1_zeros)
    #sa需要取消下面的注释
   # col2_max_zero_streak = max_consecutive_zeros(col2_zeros)
   
    # 若任一列存在连续≥8年的零值，判定为不合格
    # if col1_max_zero_streak >= zero_streak_threshold or col2_max_zero_streak >= zero_streak_threshold:
    #     print(f"{alpha_id} 不合法：存在连续{zero_streak_threshold//252}年零值")
    #     return False
    #SA取消上面的注释，注释下面的代码
    if col1_max_zero_streak >= zero_streak_threshold  >= zero_streak_threshold:
        print(f"{alpha_id} 不合法：存在连续{zero_streak_threshold//252}年零值")
        not_legal_id.append(str(alpha_id))
        return False
    # 3. 保留原有连续非零值检查
    if check_consecutive_non_zero_values(alpha_id, records)==False:
        return False
    return
def get_alpha_pnl_legal_list(fo_tracker: list) -> list:
    fo_tracker = [fo for fo in fo_tracker if get_alpha_pnl_legal(fo[0])]
    return fo_tracker
def mute(alpha_id):
    url = "https://api.worldquantbrain.com/alphas/"+alpha_id
    data = {
        "hidden": True
    }
    response = s.patch(url, json=data)
 
fo_tracker = get_alphas('07-28', '07-30', 1.0, 0.1, 'GLB', 400, 'submit')
f_num = len(fo_tracker)
print(f_num,"个alpha 进行pnl合法检测，请耐心等待")
count=0
print(len(fo_tracker))
for i in fo_tracker[::-1][0:]:
    if count%25==0:
        print('===========',count,'===========')
    count+=1
    if get_alpha_pnl_legal(i[0])==False:
        print(i[0],'已经隐藏')
        mute(i[0])
 
