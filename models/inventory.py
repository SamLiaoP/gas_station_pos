import pandas as pd
from utils.common import logger
from database import db_manager
from models.data_manager import read_inventory, save_inventory

# 添加新產品到庫存
def add_new_product(product_name, unit, quantity, unit_price, supplier):
    """添加新產品到庫存"""
    try:
        # 獲取最大產品ID
        result = db_manager.execute_query("SELECT MAX(product_id) FROM inventory")
        max_id = result[0][0] if result and result[0][0] is not None else 0
        new_id = max_id + 1
        
        # 執行插入操作
        query = """
            INSERT INTO inventory (product_id, product_name, unit, quantity, unit_price, supplier)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (new_id, product_name, unit, float(quantity), float(unit_price), supplier)
        
        db_manager.execute_command(query, params)
        
        logger.info(f"已添加新產品: {product_name}, 編號: {new_id}")
        return new_id
    except Exception as e:
        logger.error(f"添加新產品時出錯: {str(e)}")
        return None

# 更新庫存數量
def update_inventory_quantity(product_id, unit, quantity_change):
    """更新庫存數量"""
    try:
        # 先查詢當前數量
        query = """
            SELECT quantity FROM inventory
            WHERE product_id = ? AND unit = ?
        """
        params = (product_id, unit)
        
        result = db_manager.execute_query(query, params)
        
        if not result:
            logger.warning(f"找不到產品: 產品編號 {product_id}, 單位 {unit}")
            return False
        
        current_quantity = result[0][0]
        new_quantity = current_quantity + quantity_change
        
        if new_quantity <= 0:
            # 如果數量為0或負數，從庫存中刪除該產品
            query = """
                DELETE FROM inventory
                WHERE product_id = ? AND unit = ?
            """
            db_manager.execute_command(query, params)
            logger.info(f"產品已從庫存中移除: 產品編號 {product_id}, 單位 {unit}")
        else:
            # 更新數量
            query = """
                UPDATE inventory
                SET quantity = ?
                WHERE product_id = ? AND unit = ?
            """
            params = (new_quantity, product_id, unit)
            
            db_manager.execute_command(query, params)
            logger.info(f"已更新庫存數量: 產品編號 {product_id}, 單位 {unit}, 新數量 {new_quantity}")
        
        return True
    except Exception as e:
        logger.error(f"更新庫存數量時出錯: {str(e)}")
        return False

# 查找產品詳情
def get_product_details(product_name=None, product_id=None):
    """查找產品詳情"""
    try:
        if product_name:
            # 按產品名稱查詢
            query = """
                SELECT * FROM inventory
                WHERE product_name = ?
            """
            params = (product_name,)
        elif product_id:
            # 按產品編號查詢
            query = """
                SELECT * FROM inventory
                WHERE product_id = ?
            """
            params = (product_id,)
        else:
            logger.warning("查詢產品詳情時未提供產品名稱或編號")
            return None
        
        # 執行查詢並取得結果
        rows = db_manager.execute_query(query, params)
        
        if not rows:
            logger.warning(f"找不到產品: {product_name or product_id}")
            return None
        
        # 整理每種單位的產品信息
        units_info = []
        for row in rows:
            unit_info = {
                'unit': row['unit'],
                'unit_price': float(row['unit_price']),
                'quantity': float(row['quantity']),
                'product_id': int(row['product_id']),
                'supplier': row['supplier']
            }
            units_info.append(unit_info)
        
        # 創建回傳結果
        result = {
            'name': rows[0]['product_name'],
            'unit': rows[0]['unit'],  # 預設單位
            'units': [row['unit'] for row in rows],  # 所有可能的單位
            'units_info': units_info,  # 每個單位的詳細資訊
            'unit_price': float(rows[0]['unit_price']),
            'quantity': float(rows[0]['quantity']),
            'product_id': int(rows[0]['product_id']),
            'supplier': rows[0]['supplier']
        }
        
        return result
    except Exception as e:
        logger.error(f"查詢產品詳情時出錯: {str(e)}")
        return None

# 按廠商查詢產品
def get_products_by_supplier(supplier):
    """按廠商查詢產品"""
    try:
        # 查詢該廠商的產品
        query = """
            SELECT * FROM inventory
            WHERE supplier = ?
        """
        params = (supplier,)
        
        rows = db_manager.execute_query(query, params)
        
        if not rows:
            logger.warning(f"找不到廠商 {supplier} 的產品")
            return []
        
        # 整理產品列表
        products = []
        for row in rows:
            products.append({
                'product_id': int(row['product_id']),
                'name': row['product_name'],
                'unit': row['unit'],
                'quantity': float(row['quantity']),
                'price': float(row['unit_price']),
                'supplier': row['supplier']
            })
        
        return products
    except Exception as e:
        logger.error(f"按廠商查詢產品時出錯: {str(e)}")
        return []
