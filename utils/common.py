import os
import pytz
import logging
from datetime import datetime, timedelta
import shutil

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 配置文件路徑
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_PATH, 'data')
REPORTS_PATH = os.path.join(BASE_PATH, 'reports')

# 獲取台灣時間
def get_taiwan_time():
    taipei_tz = pytz.timezone('Asia/Taipei')
    return datetime.now(pytz.utc).astimezone(taipei_tz)

# 確保所有必要目錄存在
def ensure_directories():
    for path in [DATA_PATH, REPORTS_PATH]:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            logger.info(f"已創建目錄: {path}")

# 獲取當前班別
def get_current_shift():
    from models.data_manager import read_master_data
    
    # 讀取配置信息
    config_df = read_master_data('系統配置')
    
    # 組織成字典
    config = dict(zip(config_df['鍵'], config_df['值']))
    
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
