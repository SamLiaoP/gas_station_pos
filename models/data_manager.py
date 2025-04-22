import os
import pandas as pd
from utils.common import DATA_PATH, logger

# 檢查Excel文件是否存在，並創建新文件
def ensure_excel_file(file_path, sheet_name=None, columns=None):
    if os.path.exists(file_path):
        return True
    
    # 如果文件不存在，創建新的空白文件
    if sheet_name and columns:
        # 創建多sheet Excel文件
        with pd.ExcelWriter(file_path) as writer:
            df = pd.DataFrame(columns=columns)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    elif columns:
        # 創建單一sheet Excel文件
        df = pd.DataFrame(columns=columns)
        df.to_excel(file_path, index=False)
    else:
        # 沒有指定列名，創建一個最基本的空白Excel
        pd.DataFrame().to_excel(file_path, index=False)
    
    logger.info(f"已創建新的Excel文件: {file_path}")
    return True

# 確保主數據文件存在，如果不存在則創建初始數據
def ensure_master_data():
    # 主數據文件路徑
    master_data_path = os.path.join(DATA_PATH, 'master_data.xlsx')
    
    # 如果文件已存在，直接返回
    if os.path.exists(master_data_path):
        return True
    
    # 如果不存在，創建初始數據
    try:
        # 創建系統配置表
        config_df = pd.DataFrame({
            '鍵': ['morning_shift_start', 'morning_shift_end', 'afternoon_shift_start', 'afternoon_shift_end', 'night_shift_start', 'night_shift_end'],
            '值': ['06:00', '14:00', '14:00', '22:00', '22:00', '06:00']
        })
        
        # 創建員工廠商表
        staff_farmers_df = pd.DataFrame({
            '類型': ['staff', 'staff', 'staff', 'farmer', 'farmer', 'farmer'],
            '名稱': ['王小明', '李小華', '張大力', '有機農場', '綠色蔬果', '友善耕作'],
            '分潤比例': [0.05, 0.05, 0.05, 0.15, 0.12, 0.10]
        })
        
        # 創建一個Excel文件，包含多個工作表
        with pd.ExcelWriter(master_data_path) as writer:
            config_df.to_excel(writer, sheet_name='系統配置', index=False)
            staff_farmers_df.to_excel(writer, sheet_name='員工廠商', index=False)
        
        logger.info(f"已創建主數據文件: {master_data_path}")
        return True
    except Exception as e:
        logger.error(f"創建主數據時出錯: {str(e)}")
        return False

# 確保庫存文件存在，如果不存在則創建初始數據
def ensure_inventory_data():
    # 庫存文件路徑
    inventory_path = os.path.join(DATA_PATH, 'inventory.xlsx')
    
    # 如果文件已存在，直接返回
    if os.path.exists(inventory_path):
        return True
    
    # 如果不存在，創建初始數據
    try:
        # 創建庫存表
        inventory_df = pd.DataFrame({
            '產品編號': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            '產品名稱': ['有機小白菜', '有機青菜', '有機紅蘿蔔', '有機紅蘿蔔', '有機番茄', '有機番茄', '有機馬鈴薯', '新鮮蘋果', '新鮮蘋果', '新鮮蘋果'],
            '單位': ['把', '把', '公斤', '條', '公斤', '顆', '公斤', '顆', '箱', '公斤'],
            '數量': [20, 15, 30, 40, 25, 50, 40, 50, 5, 10],
            '單價': [35, 30, 60, 20, 70, 15, 45, 20, 400, 80],
            '供應商': ['有機農場', '有機農場', '綠色蔬果', '綠色蔬果', '綠色蔬果', '綠色蔬果', '友善耕作', '有機農場', '有機農場', '有機農場']
        })
        
        # 保存到文件
        inventory_df.to_excel(inventory_path, index=False)
        
        logger.info(f"已創建庫存文件: {inventory_path}")
        return True
    except Exception as e:
        logger.error(f"創建庫存數據時出錯: {str(e)}")
        return False

# 確保交易記錄文件存在
def ensure_transactions_data():
    # 交易記錄文件路徑
    transactions_path = os.path.join(DATA_PATH, 'transactions.xlsx')
    
    # 如果文件已存在，直接返回
    if os.path.exists(transactions_path):
        return True
    
    # 如果不存在，創建空文件
    try:
        # 設置標準列名
        transaction_columns = [
            '交易ID', '交易類型', '日期', '時間', '員工', '班別',
            '產品編號', '產品名稱', '單位', '數量', '單價', '總價', 
            '供應商', '退貨原因'
        ]
        
        # 創建空的交易記錄
        transactions_df = pd.DataFrame(columns=transaction_columns)
        transactions_df.to_excel(transactions_path, index=False)
        
        logger.info(f"已創建交易記錄文件: {transactions_path}")
        return True
    except Exception as e:
        logger.error(f"創建交易記錄數據時出錯: {str(e)}")
        return False

# 讀取主數據文件中的指定sheet
def read_master_data(sheet_name):
    master_data_path = os.path.join(DATA_PATH, 'master_data.xlsx')
    ensure_master_data()  # 確保文件存在
    
    try:
        return pd.read_excel(master_data_path, sheet_name=sheet_name)
    except Exception as e:
        logger.error(f"讀取主數據 {sheet_name} 時出錯: {str(e)}")
        return pd.DataFrame()

# 讀取庫存數據
def read_inventory():
    inventory_path = os.path.join(DATA_PATH, 'inventory.xlsx')
    ensure_inventory_data()  # 確保文件存在
    
    try:
        return pd.read_excel(inventory_path)
    except Exception as e:
        logger.error(f"讀取庫存數據時出錯: {str(e)}")
        return pd.DataFrame()

# 讀取交易記錄
def read_transactions(transaction_type=None, start_date=None, end_date=None):
    transactions_path = os.path.join(DATA_PATH, 'transactions.xlsx')
    ensure_transactions_data()  # 確保文件存在
    
    try:
        df = pd.read_excel(transactions_path)
        
        # 根據交易類型過濾
        if transaction_type:
            df = df[df['交易類型'] == transaction_type]
        
        # 根據日期範圍過濾
        if start_date and end_date:
            df = df[(df['日期'] >= start_date) & (df['日期'] <= end_date)]
        elif start_date:
            df = df[df['日期'] >= start_date]
        elif end_date:
            df = df[df['日期'] <= end_date]
        
        return df
    except Exception as e:
        logger.error(f"讀取交易記錄時出錯: {str(e)}")
        return pd.DataFrame()

# 保存主數據
def save_master_data(df, sheet_name):
    master_data_path = os.path.join(DATA_PATH, 'master_data.xlsx')
    ensure_master_data()  # 確保文件存在
    
    try:
        # 讀取所有工作表數據
        with pd.ExcelFile(master_data_path) as xls:
            sheet_names = xls.sheet_names
            sheet_data = {name: pd.read_excel(master_data_path, sheet_name=name) for name in sheet_names}
        
        # 更新特定工作表數據
        sheet_data[sheet_name] = df
        
        # 保存所有工作表
        with pd.ExcelWriter(master_data_path) as writer:
            for name, data in sheet_data.items():
                data.to_excel(writer, sheet_name=name, index=False)
        
        logger.info(f"已更新主數據 {sheet_name}")
        return True
    except Exception as e:
        logger.error(f"保存主數據 {sheet_name} 時出錯: {str(e)}")
        return False

# 保存庫存數據
def save_inventory(df):
    inventory_path = os.path.join(DATA_PATH, 'inventory.xlsx')
    
    try:
        df.to_excel(inventory_path, index=False)
        logger.info("已更新庫存數據")
        return True
    except Exception as e:
        logger.error(f"保存庫存數據時出錯: {str(e)}")
        return False

# 添加交易記錄
def add_transaction(transaction_data):
    transactions_path = os.path.join(DATA_PATH, 'transactions.xlsx')
    ensure_transactions_data()  # 確保文件存在
    
    try:
        # 讀取現有交易記錄
        df = pd.read_excel(transactions_path)
        
        # 生成交易ID
        if df.empty:
            transaction_id = 1
        else:
            transaction_id = df['交易ID'].max() + 1
        
        # 添加交易ID到數據中
        transaction_data['交易ID'] = transaction_id
        
        # 添加新的交易記錄
        new_transaction = pd.DataFrame([transaction_data])
        df = pd.concat([df, new_transaction], ignore_index=True)
        
        # 保存更新後的交易記錄
        df.to_excel(transactions_path, index=False)
        
        logger.info(f"已添加交易記錄，ID: {transaction_id}")
        return transaction_id
    except Exception as e:
        logger.error(f"添加交易記錄時出錯: {str(e)}")
        return None

# 獲取員工和廠商列表
def get_staff_and_farmers():
    staff_farmers_df = read_master_data('員工廠商')
    
    staff = staff_farmers_df[staff_farmers_df['類型'] == 'staff']['名稱'].tolist()
    farmers = staff_farmers_df[staff_farmers_df['類型'] == 'farmer']['名稱'].tolist()
    
    return staff, farmers
