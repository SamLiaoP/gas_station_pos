import pandas as pd
import os
from datetime import datetime
import pytz

# 獲取台灣時間
def get_taiwan_time():
    taipei_tz = pytz.timezone('Asia/Taipei')
    return datetime.now(pytz.utc).astimezone(taipei_tz)

# 當前時間戳記
current_time = get_taiwan_time().strftime('%Y-%m-%d %H:%M:%S')

# 確保數據目錄存在
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

# 1. 員工和小農表
staff_farmers_df = pd.DataFrame({
    '類型': ['staff', 'staff', 'staff', 'farmer', 'farmer', 'farmer'],
    '名稱': ['王小明', '李小華', '張大力', '有機農場', '綠色蔬果', '友善耕作'],
    '分潤比例': [0.05, 0.05, 0.05, 0.15, 0.12, 0.10]
})

# 2. 庫存表 - 特別修改：為同一產品添加多個單位版本
inventory_df = pd.DataFrame({
    '產品編號': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    '產品名稱': ['有機小白菜', '有機青菜', '有機紅蘿蔔', '有機紅蘿蔔', '有機番茄', '有機番茄', '有機馬鈴薯', '新鮮蘋果', '新鮮蘋果', '新鮮蘋果'],
    '單位': ['把', '把', '公斤', '條', '公斤', '顆', '公斤', '顆', '箱', '公斤'],
    '數量': [20, 15, 30, 40, 25, 50, 40, 50, 5, 10],
    '單價': [35, 30, 60, 20, 70, 15, 45, 20, 400, 80],
    '供應商': ['有機農場', '有機農場', '綠色蔬果', '綠色蔬果', '綠色蔬果', '綠色蔬果', '友善耕作', '有機農場', '有機農場', '有機農場']
})

# 3. 進貨表 (添加時間戳記欄位)
purchase_df = pd.DataFrame(columns=[
    '日期', '時間戳記', '供應商', '產品名稱', '單位', '數量', '單價', '總價', '收貨員工'
])

# 4. 銷售表 (添加時間戳記欄位)
sales_df = pd.DataFrame(columns=[
    '日期', '時間戳記', '班別', '員工', '產品名稱', '單位', '數量', '單價', '總價'
])

# 5. 配置文件
config_df = pd.DataFrame({
    '鍵': ['morning_shift_start', 'morning_shift_end', 'afternoon_shift_start', 'afternoon_shift_end', 'night_shift_start', 'night_shift_end'],
    '值': ['06:00', '14:00', '14:00', '22:00', '22:00', '06:00']
})

# 儲存檔案
staff_farmers_df.to_excel(os.path.join(DATA_PATH, 'staff_farmers.xlsx'), index=False)
inventory_df.to_excel(os.path.join(DATA_PATH, 'inventory.xlsx'), index=False)
purchase_df.to_excel(os.path.join(DATA_PATH, 'purchases.xlsx'), index=False)
sales_df.to_excel(os.path.join(DATA_PATH, 'sales.xlsx'), index=False)
config_df.to_excel(os.path.join(DATA_PATH, 'config.xlsx'), index=False)

print("所有Excel檔案的欄位已更新為繁體中文，並添加時間戳記欄位！")
print("特別修改：為部分產品添加了多單位版本：")
print("- 有機紅蘿蔔: 公斤、條")
print("- 有機番茄: 公斤、顆")
print("- 新鮮蘋果: 顆、箱、公斤")
