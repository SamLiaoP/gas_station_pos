import os
import pandas as pd
import shutil
import pytz
from datetime import datetime
from app import app

# 獲取台灣時間
def get_taiwan_time():
    taipei_tz = pytz.timezone('Asia/Taipei')
    return datetime.now(pytz.utc).astimezone(taipei_tz)

# 今日日期
today_date = get_taiwan_time().strftime('%Y-%m-%d')

# 基本路徑設置
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
ARCHIVES_PATH = os.path.join(BASE_PATH, 'archives')
REPORTS_PATH = os.path.join(BASE_PATH, 'reports')
STORAGE_PATH = os.path.join(BASE_PATH, 'storage')
TODAY_STORAGE_PATH = os.path.join(STORAGE_PATH, today_date)
DATA_PATH = os.path.join(TODAY_STORAGE_PATH, 'data')

# 確保所有必要的目錄都存在
for path in [ARCHIVES_PATH, REPORTS_PATH, STORAGE_PATH, TODAY_STORAGE_PATH, DATA_PATH]:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        print(f"已創建目錄: {path}")

# 檢查是否需要從最新的封存複製數據文件
def copy_from_latest_archive():
    try:
        # 檢查是否有封存目錄
        if os.path.exists(ARCHIVES_PATH) and os.listdir(ARCHIVES_PATH):
            # 獲取最近的封存日期
            archive_dates = sorted([d for d in os.listdir(ARCHIVES_PATH) if os.path.isdir(os.path.join(ARCHIVES_PATH, d))], reverse=True)
            
            if archive_dates:
                latest_date = archive_dates[0]
                latest_archive_path = os.path.join(ARCHIVES_PATH, latest_date)
                
                # 檢查今日數據文件是否已經存在
                files_to_check = ['staff_farmers.xlsx', 'inventory.xlsx', 'config.xlsx']
                files_exist = all(os.path.exists(os.path.join(DATA_PATH, f)) for f in files_to_check)
                
                if not files_exist:
                    print(f"今日({today_date})數據文件不存在，從最近的封存({latest_date})中複製")
                    
                    # 複製最新的封存文件到今日目錄
                    for file_name in files_to_check:
                        src_file = os.path.join(latest_archive_path, file_name)
                        dst_file = os.path.join(DATA_PATH, file_name)
                        
                        if os.path.exists(src_file):
                            shutil.copy2(src_file, dst_file)
                            print(f"已複製 {file_name} 從封存到今日目錄")
                    
                    # 創建空的進銷記錄檔案
                    empty_purchase = pd.DataFrame(columns=['日期', '時間戳記', '供應商', '產品名稱', '單位', '數量', '單價', '總價', '收貨員工'])
                    empty_purchase.to_excel(os.path.join(DATA_PATH, 'purchases.xlsx'), index=False)
                    
                    empty_sales = pd.DataFrame(columns=['日期', '時間戳記', '班別', '員工', '產品名稱', '單位', '數量', '單價', '總價'])
                    empty_sales.to_excel(os.path.join(DATA_PATH, 'sales.xlsx'), index=False)
                    
                    print("已創建今日空白的進銷記錄檔案")
                    return True
                else:
                    print(f"今日({today_date})數據文件已存在，無需從封存複製")
                    return True
    except Exception as e:
        print(f"從封存複製數據時出錯: {str(e)}")
    
    return False

# 創建初始數據文件
def create_initial_files():
    # 檢查是否已有封存數據可以複製
    if copy_from_latest_archive():
        return
    
    # 如果沒有封存數據，創建新的數據文件
    files_to_check = {
        'staff_farmers.xlsx': pd.DataFrame({
            '類型': ['staff', 'staff', 'staff', 'farmer', 'farmer', 'farmer'],
            '名稱': ['王小明', '李小華', '張大力', '有機農場', '綠色蔬果', '友善耕作'],
            '分潤比例': [0.05, 0.05, 0.05, 0.15, 0.12, 0.10]
        }),
        'inventory.xlsx': pd.DataFrame({
            '產品編號': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            '產品名稱': ['有機小白菜', '有機青菜', '有機紅蘿蔔', '有機紅蘿蔔', '有機番茄', '有機番茄', '有機馬鈴薯', '新鮮蘋果', '新鮮蘋果', '新鮮蘋果'],
            '單位': ['把', '把', '公斤', '條', '公斤', '顆', '公斤', '顆', '箱', '公斤'],
            '數量': [20, 15, 30, 40, 25, 50, 40, 50, 5, 10],
            '單價': [35, 30, 60, 20, 70, 15, 45, 20, 400, 80],
            '供應商': ['有機農場', '有機農場', '綠色蔬果', '綠色蔬果', '綠色蔬果', '綠色蔬果', '友善耕作', '有機農場', '有機農場', '有機農場']
        }),
        'purchases.xlsx': pd.DataFrame(columns=[
            '日期', '時間戳記', '供應商', '產品名稱', '單位', '數量', '單價', '總價', '收貨員工'
        ]),
        'sales.xlsx': pd.DataFrame(columns=[
            '日期', '時間戳記', '班別', '員工', '產品名稱', '單位', '數量', '單價', '總價'
        ]),
        'config.xlsx': pd.DataFrame({
            '鍵': ['morning_shift_start', 'morning_shift_end', 'afternoon_shift_start', 'afternoon_shift_end', 'night_shift_start', 'night_shift_end'],
            '值': ['06:00', '14:00', '14:00', '22:00', '22:00', '06:00']
        })
    }
    
    for file_name, df in files_to_check.items():
        file_path = os.path.join(DATA_PATH, file_name)
        if not os.path.exists(file_path):
            df.to_excel(file_path, index=False)
            print(f"已創建初始 {file_name}")

# 檢查舊有的數據目錄
def migrate_old_data():
    old_data_path = os.path.join(BASE_PATH, 'data')
    if os.path.exists(old_data_path) and os.path.isdir(old_data_path):
        print("檢測到舊版數據目錄，正在遷移...")
        
        # 創建舊數據的封存目錄
        old_archive_path = os.path.join(ARCHIVES_PATH, 'migrated_old_data')
        os.makedirs(old_archive_path, exist_ok=True)
        
        # 複製舊數據到封存
        for file_name in os.listdir(old_data_path):
            src_file = os.path.join(old_data_path, file_name)
            dst_file = os.path.join(old_archive_path, file_name)
            if os.path.isfile(src_file):
                shutil.copy2(src_file, dst_file)
                print(f"已複製舊數據文件 {file_name} 到封存目錄")
        
        # 如果今日目錄為空，也複製到今日目錄
        if not os.listdir(DATA_PATH):
            for file_name in os.listdir(old_data_path):
                src_file = os.path.join(old_data_path, file_name)
                dst_file = os.path.join(DATA_PATH, file_name)
                if os.path.isfile(src_file):
                    shutil.copy2(src_file, dst_file)
                    print(f"已複製舊數據文件 {file_name} 到今日目錄")
        
        print("舊數據遷移完成，已保留原始目錄。您可以在確認新系統運行正常後手動刪除舊目錄。")

# 運行初始化
print(f"===== 加油站小農POS系統初始化 ({today_date}) =====")
migrate_old_data()
create_initial_files()
print("數據初始化完成")

# 啟動應用
if __name__ == '__main__':
    print("啟動加油站小農POS系統，請訪問 http://127.0.0.1:8080/")
    # 如果需要在區域網內裡訪問，請將host設為'0.0.0.0'
    # 如果只在本機訪問，請使用'127.0.0.1'
    app.run(debug=True, host='0.0.0.0', port=8080)
