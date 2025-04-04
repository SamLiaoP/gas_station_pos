import os
import pandas as pd
from models.data_manager import get_inventory
from utils.common import DATA_PATH, logger

# 更新庫存
def update_inventory(product_name, change_quantity):
    file_path = os.path.join(DATA_PATH, 'inventory.xlsx')
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        if product_name in df['產品名稱'].values:
            idx = df[df['產品名稱'] == product_name].index[0]
            df.at[idx, '數量'] = df.at[idx, '數量'] + change_quantity
            
            # 如果庫存為0，則移除該產品
            if df.at[idx, '數量'] <= 0:
                df = df.drop(idx)
                
            df.to_excel(file_path, index=False)
            return True
    return False

# 添加新產品到庫存
def add_new_product(product_name, unit, quantity, unit_price, farmer):
    file_path = os.path.join(DATA_PATH, 'inventory.xlsx')
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        new_id = 1
        if not df.empty:
            new_id = df['產品編號'].max() + 1
        
        new_row = pd.DataFrame({
            '產品編號': [new_id],
            '產品名稱': [product_name],
            '單位': [unit],
            '數量': [quantity],
            '單價': [unit_price],
            '供應商': [farmer]
        })
        
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_excel(file_path, index=False)
        return True
    return False

# 獲取產品詳情
def get_product_details(product_name):
    inventory = get_inventory()
    logger.info(f"獲取產品詳情，產品名稱: '{product_name}'")
    logger.info(f"當前庫存中的產品列表: {inventory['產品名稱'].unique().tolist()}")
    
    if product_name in inventory['產品名稱'].values:
        # 獲取符合產品名稱的所有行
        product_rows = inventory[inventory['產品名稱'] == product_name]
        logger.info(f"找到產品 '{product_name}' 的資料行數: {len(product_rows)}")
        
        # 取第一個產品的基本信息
        product = product_rows.iloc[0]
        logger.info(f"產品基本信息: {product.to_dict()}")
        
        # 獲取該產品的所有可能單位
        units = product_rows['單位'].unique().tolist()
        logger.info(f"產品所有單位: {units}")
        
        # 為每個單位創建詳細資訊列表
        units_info = []
        for unit in units:
            unit_rows = product_rows[product_rows['單位'] == unit]
            if not unit_rows.empty:
                unit_row = unit_rows.iloc[0]
                unit_info = {
                    'unit': unit,
                    'unit_price': float(unit_row['單價']),
                    'quantity': float(unit_row['數量']),
                    'product_id': int(unit_row['產品編號'])
                }
                units_info.append(unit_info)
                logger.info(f"單位 '{unit}' 詳情: {unit_info}")
            else:
                logger.warning(f"找不到單位 '{unit}' 的資料")
        
        # 創建回傳結果
        result = {
            'unit': product['單位'],       # 預設單位
            'units': units,                # 所有可能的單位
            'units_info': units_info,      # 每個單位的詳細資訊
            'unit_price': float(product['單價']),
            'quantity': float(product['數量']),
            'product_id': int(product['產品編號'])
        }
        logger.info(f"回傳結果: {result}")
        return result
    logger.warning(f"庫存中找不到產品: '{product_name}'")
    return None
