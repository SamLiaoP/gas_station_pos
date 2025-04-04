import os
import pytz
from datetime import datetime, timedelta
import logging
import shutil
import traceback

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 配置文件路徑
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVES_PATH = os.path.join(BASE_PATH, 'archives')
REPORTS_PATH = os.path.join(BASE_PATH, 'reports')
STORAGE_PATH = os.path.join(BASE_PATH, 'storage')

# 獲取台灣時間
def get_taiwan_time():
    taipei_tz = pytz.timezone('Asia/Taipei')
    return datetime.now(pytz.utc).astimezone(taipei_tz)

# 今日日期
today_date = get_taiwan_time().strftime('%Y-%m-%d')

# 今日數據路徑
DATA_PATH = os.path.join(STORAGE_PATH, today_date, 'data')

# 確保所有必要目錄存在
def ensure_directories():
    for path in [REPORTS_PATH, ARCHIVES_PATH, STORAGE_PATH, DATA_PATH]:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            logger.info(f"已創建目錄: {path}")

# 將昨日數據移至封存資料夾
def archive_yesterday_data():
    try:
        # 計算昨日日期
        yesterday = (get_taiwan_time() - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_data_path = os.path.join(STORAGE_PATH, yesterday, 'data')
        
        # 檢查昨日數據是否存在
        if os.path.exists(yesterday_data_path):
            # 創建昨日的封存目錄
            archive_path = os.path.join(ARCHIVES_PATH, yesterday)
            os.makedirs(archive_path, exist_ok=True)
            
            # 複製昨日數據到封存目錄
            for file_name in os.listdir(yesterday_data_path):
                src_file = os.path.join(yesterday_data_path, file_name)
                dst_file = os.path.join(archive_path, file_name)
                if os.path.isfile(src_file):
                    shutil.copy2(src_file, dst_file)
            
            logger.info(f"已將昨日({yesterday})數據封存至 {archive_path}")
            return True
    except Exception as e:
        logger.error(f"封存昨日數據時出錯: {str(e)}")
        logger.error(traceback.format_exc())
        return False
