import pandas as pd
import os

# 設定基本路徑
base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# 確保目錄存在
os.makedirs(base_dir, exist_ok=True)

# 1. 創建主數據文件 - 系統配置、員工和廠商信息
config_df = pd.DataFrame({
    '鍵': ['morning_shift_start', 'morning_shift_end', 'afternoon_shift_start', 'afternoon_shift_end', 'night_shift_start', 'night_shift_end'],
    '值': ['06:00', '14:00', '14:00', '22:00', '22:00', '06:00']
})

staff_farmers_df = pd.DataFrame({
    '類型': ['staff', 'staff', 'staff', 'farmer', 'farmer', 'farmer'],
    '名稱': ['王小明', '李小華', '張大力', '有機農場', '綠色蔬果', '友善耕作'],
    '分潤比例': [0.05, 0.05, 0.05, 0.15, 0.12, 0.10]
})

# 創建一個Excel文件，包含多個工作表
with pd.ExcelWriter(os.path.join(base_dir, 'master_data.xlsx')) as writer:
    config_df.to_excel(writer, sheet_name='系統配置', index=False)
    staff_farmers_df.to_excel(writer, sheet_name='員工廠商', index=False)

print(f"已創建主數據文件: {os.path.join(base_dir, 'master_data.xlsx')}")

# 2. 創建庫存文件
inventory_df = pd.DataFrame({
    '產品編號': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    '產品名稱': ['有機小白菜', '有機青菜', '有機紅蘿蔔', '有機紅蘿蔔', '有機番茄', '有機番茄', '有機馬鈴薯', '新鮮蘋果', '新鮮蘋果', '新鮮蘋果'],
    '單位': ['把', '把', '公斤', '條', '公斤', '顆', '公斤', '顆', '箱', '公斤'],
    '數量': [20, 15, 30, 40, 25, 50, 40, 50, 5, 10],
    '單價': [35, 30, 60, 20, 70, 15, 45, 20, 400, 80],
    '供應商': ['有機農場', '有機農場', '綠色蔬果', '綠色蔬果', '綠色蔬果', '綠色蔬果', '友善耕作', '有機農場', '有機農場', '有機農場']
})

inventory_df.to_excel(os.path.join(base_dir, 'inventory.xlsx'), index=False)
print(f"已創建庫存文件: {os.path.join(base_dir, 'inventory.xlsx')}")

# 3. 創建一個整合的交易記錄文件，包含不同類型的交易
# 設置標準列名
transaction_columns = [
    '交易ID', '交易類型', '日期', '時間', '員工', '班別',
    '產品編號', '產品名稱', '單位', '數量', '單價', '總價', 
    '供應商', '退貨原因'
]

# 創建空的交易記錄
transactions_df = pd.DataFrame(columns=transaction_columns)
transactions_df.to_excel(os.path.join(base_dir, 'transactions.xlsx'), index=False)
print(f"已創建交易記錄文件: {os.path.join(base_dir, 'transactions.xlsx')}")

print("資料初始化完成")
