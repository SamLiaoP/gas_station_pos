import os
import pandas as pd
from utils.common import DATA_PATH, get_taiwan_time, logger

# 讀取配置文件
def get_config():
    config_file = os.path.join(DATA_PATH, 'config.xlsx')
    if os.path.exists(config_file):
        df = pd.read_excel(config_file)
        config = dict(zip(df['鍵'], df['值']))
        return config
    return {}

# 獲取當前班別
def get_current_shift():
    config = get_config()
    now = get_taiwan_time().time()
    now_str = now.strftime('%H:%M')
    
    # 轉換時間為分鐘表示，方便比較
    def time_to_minutes(time_str):
        h, m = map(int, time_str.split(':'))
        return h * 60 + m
    
    now_minutes = time_to_minutes(now_str)
    
    morning_start = time_to_minutes(config.get('morning_shift_start', '06:00'))
    morning_end = time_to_minutes(config.get('morning_shift_end', '14:00'))
    afternoon_start = time_to_minutes(config.get('afternoon_shift_start', '14:00'))
    afternoon_end = time_to_minutes(config.get('afternoon_shift_end', '22:00'))
    
    # 判斷當前班別
    if morning_start <= now_minutes < morning_end:
        return '早班'
    elif afternoon_start <= now_minutes < afternoon_end:
        return '午班'
    else:
        return '晚班'
