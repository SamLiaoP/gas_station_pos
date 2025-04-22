import pandas as pd
from models.data_manager import read_inventory, save_inventory, logger

# 添加新產品到庫存
def add_new_product(product_name, unit, quantity, unit_price, supplier):
    # 讀取當前庫存
    inventory_df = read_inventory()
    
    # 生成新的產品編號
    if inventory_df.empty:
        new_id = 1
    else:
        new_id = inventory_df['產品編號'].max() + 1
    
    # 創建新產品記錄
    new_product = pd.DataFrame({
        '產品編號': [new_id],
        '產品名稱': [product_name],
        '單位': [unit],
        '數量': [quantity],
        '單價': [unit_price],
        '供應商': [supplier]
    })
    
    # 添加到庫存
    inventory_df = pd.concat([inventory_df, new_product], ignore_index=True)
    
    # 保存更新後的庫存
    save_inventory(inventory_df)
    
    logger.info(f"已添加新產品: {product_name}, 編號: {new_id}")
    return new_id

# 更新庫存數量
def update_inventory_quantity(product_id, unit, quantity_change):
    # 讀取當前庫存
    inventory_df = read_inventory()
    
    # 查找產品
    mask = (inventory_df['產品編號'] == product_id) & (inventory_df['單位'] == unit)
    if mask.any():
        # 找到產品，更新數量
        index = mask.idxmax()
        current_quantity = inventory_df.at[index, '數量']
        new_quantity = current_quantity + quantity_change
        
        if new_quantity <= 0:
            # 如果數量為0或負數，從庫存中移除該產品
            inventory_df = inventory_df.drop(index)
            logger.info(f"產品已從庫存中移除: 產品編號 {product_id}, 單位 {unit}")
        else:
            # 更新數量
            inventory_df.at[index, '數量'] = new_quantity
            logger.info(f"已更新庫存數量: 產品編號 {product_id}, 單位 {unit}, 新數量 {new_quantity}")
        
        # 保存更新後的庫存
        save_inventory(inventory_df)
        return True
    else:
        logger.warning(f"找不到產品: 產品編號 {product_id}, 單位 {unit}")
        return False

# 查找產品詳情
def get_product_details(product_name=None, product_id=None):
    # 讀取當前庫存
    inventory_df = read_inventory()
    
    if product_name:
        # 按產品名稱查找
        product_rows = inventory_df[inventory_df['產品名稱'] == product_name]
    elif product_id:
        # 按產品編號查找
        product_rows = inventory_df[inventory_df['產品編號'] == product_id]
    else:
        logger.warning("查詢產品詳情時未提供產品名稱或編號")
        return None
    
    if product_rows.empty:
        logger.warning(f"找不到產品: {product_name or product_id}")
        return None
    
    # 獲取該產品的所有單位
    units_info = []
    for _, row in product_rows.iterrows():
        unit_info = {
            'unit': row['單位'],
            'unit_price': float(row['單價']),
            'quantity': float(row['數量']),
            'product_id': int(row['產品編號']),
            'supplier': row['供應商']
        }
        units_info.append(unit_info)
    
    # 創建回傳結果
    result = {
        'name': product_rows.iloc[0]['產品名稱'],
        'unit': product_rows.iloc[0]['單位'],  # 預設單位
        'units': product_rows['單位'].unique().tolist(),  # 所有可能的單位
        'units_info': units_info,  # 每個單位的詳細資訊
        'unit_price': float(product_rows.iloc[0]['單價']),
        'quantity': float(product_rows.iloc[0]['數量']),
        'product_id': int(product_rows.iloc[0]['產品編號']),
        'supplier': product_rows.iloc[0]['供應商']
    }
    
    return result

# 按廠商查詢產品
def get_products_by_supplier(supplier):
    # 讀取當前庫存
    inventory_df = read_inventory()
    
    # 篩選該廠商的產品
    supplier_products = inventory_df[inventory_df['供應商'] == supplier]
    
    if supplier_products.empty:
        logger.warning(f"找不到廠商 {supplier} 的產品")
        return []
    
    # 整理產品列表
    products = []
    for _, row in supplier_products.iterrows():
        products.append({
            'product_id': int(row['產品編號']),
            'name': row['產品名稱'],
            'unit': row['單位'],
            'quantity': float(row['數量']),
            'price': float(row['單價']),
            'supplier': row['供應商']
        })
    
    return products
