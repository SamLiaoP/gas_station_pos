import os
import pandas as pd
from models.data_manager import get_inventory, ensure_data_file_exists
from models.inventory import update_inventory, add_new_product
from utils.common import DATA_PATH, get_taiwan_time

# 記錄進貨
def record_purchase(date, farmer, product_name, unit, quantity, unit_price, staff):
    total_price = quantity * unit_price
    # 獲取台灣時間戳記
    current_time = get_taiwan_time().strftime('%Y-%m-%d %H:%M:%S')
    
    # 確保進貨記錄檔案存在
    columns = ['日期', '時間戳記', '供應商', '產品名稱', '單位', '數量', '單價', '總價', '收貨員工']
    df = ensure_data_file_exists('purchases.xlsx', columns)
    
    new_row = pd.DataFrame({
        '日期': [date],
        '時間戳記': [current_time],
        '供應商': [farmer],
        '產品名稱': [product_name],
        '單位': [unit],
        '數量': [quantity],
        '單價': [unit_price],
        '總價': [total_price],
        '收貨員工': [staff]
    })
    
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel(os.path.join(DATA_PATH, 'purchases.xlsx'), index=False)
    
    # 檢查庫存中是否已有此產品
    inventory = get_inventory()
    # 檢查相同名稱和單位的產品
    matching_rows = inventory[(inventory['產品名稱'] == product_name) & (inventory['單位'] == unit)]
    
    if not matching_rows.empty:
        # 找到對應的產品，更新庫存
        idx = matching_rows.index[0]
        inventory.at[idx, '數量'] = inventory.at[idx, '數量'] + quantity
        inventory.to_excel(os.path.join(DATA_PATH, 'inventory.xlsx'), index=False)
    else:
        # 添加新產品
        add_new_product(product_name, unit, quantity, unit_price, farmer)
    
    return True

# 記錄銷售
def record_sale(date, shift, staff, product_name, unit, quantity, unit_price):
    total_price = quantity * unit_price
    # 獲取台灣時間戳記
    current_time = get_taiwan_time().strftime('%Y-%m-%d %H:%M:%S')
    
    # 確保銷售記錄檔案存在
    columns = ['日期', '時間戳記', '班別', '員工', '產品名稱', '單位', '數量', '單價', '總價']
    df = ensure_data_file_exists('sales.xlsx', columns)
    
    new_row = pd.DataFrame({
        '日期': [date],
        '時間戳記': [current_time],
        '班別': [shift],
        '員工': [staff],
        '產品名稱': [product_name],
        '單位': [unit],
        '數量': [quantity],
        '單價': [unit_price],
        '總價': [total_price]
    })
    
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel(os.path.join(DATA_PATH, 'sales.xlsx'), index=False)
    
    # 更新庫存
    # 找到對應單位的庫存記錄
    inventory = get_inventory()
    matching_rows = inventory[(inventory['產品名稱'] == product_name) & (inventory['單位'] == unit)]
    
    if not matching_rows.empty:
        # 找到對應的單位庫存，更新它
        idx = matching_rows.index[0]
        inventory.at[idx, '數量'] = inventory.at[idx, '數量'] - quantity
        
        # 如果庫存為0，則移除該產品
        if inventory.at[idx, '數量'] <= 0:
            inventory = inventory.drop(idx)
            
        inventory.to_excel(os.path.join(DATA_PATH, 'inventory.xlsx'), index=False)
    
    return True
