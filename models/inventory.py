import pandas as pd
from utils.common import logger
from database import db_manager
from models.data_manager import read_inventory, save_inventory
from typing import Optional

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
    """按廠商查詢產品 (從當前庫存)"""
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

def get_product_names_from_purchase_history(supplier_name: str) -> list[str]:
    """
    從交易記錄中獲取指定供應商曾經進貨過的所有產品名稱列表 (不重複)。
    用於銷貨退回時，確保可以選擇歷史上曾銷售過的產品，而不僅限於當前庫存。
    """
    try:
        # 假設 transactions 表的相關欄位名為: supplier, product_name, transaction_type
        query = """
            SELECT DISTINCT product_name 
            FROM transactions 
            WHERE supplier = ? AND transaction_type = '進貨'
        """
        params = (supplier_name,)
        results = db_manager.execute_query(query, params)

        if results:
            product_names = [row[0] for row in results if row and row[0] is not None]
            logger.info(f"為供應商 '{supplier_name}' 從進貨歷史中找到產品: {product_names}")
            return product_names
        else:
            logger.warning(f"供應商 '{supplier_name}' 沒有找到任何進貨歷史記錄。")
            return []
    except Exception as e:
        logger.error(f"從進貨歷史獲取供應商 '{supplier_name}' 的產品名稱時出錯: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def get_product_avg_purchase_price(product_name: str, unit: str) -> Optional[float]:
    """
    計算指定產品和單位的平均進貨單價。
    """
    try:
        # 從 transactions 表中讀取所有 '進貨' 記錄
        # 假設 transactions 表的結構與 db_manager.add_transaction 中的 db_transaction_data 一致
        # 並且 transaction_type 欄位名為 '交易類型'
        query = """
            SELECT AVG(unit_price) 
            FROM transactions 
            WHERE product_name = ? AND unit = ? AND transaction_type = '進貨'
        """ # 這裡的欄位名稱需要與資料庫中的實際名稱一致
        # 如果 add_transaction 使用的鍵名是英文 (如 'type', 'product_name', 'unit_price')，這裡也要對應修改
        # 例如: SELECT AVG(單價) FROM transactions WHERE 產品名稱 = ? AND 單位 = ? AND 交易類型 = '進貨'

        # 假設 transactions 表中 `transaction_type` 欄位名是 '交易類型'，
        # `product_name` 是 '產品名稱', `unit` 是 '單位', `unit_price` 是 '單價'
        # 這些欄位名稱需要與 db_manager.py 中 add_transaction 函數寫入資料庫時的欄位名完全一致。
        
        # 為了安全起見，我們先讀取所有相關進貨記錄，然後用 pandas 計算平均值
        # 這樣可以避免SQL注入，並且更容易處理欄位名不一致的問題（如果 data_manager.read_transactions 能返回 DataFrame 的話）
        # 但目前沒有 data_manager.read_transactions 的實現細節，先用直接SQL查詢

        # 再次確認：db_manager.execute_query 返回的是元組列表。
        # `transactions` 表的欄位名是： `id`, `transaction_type`, `date`, `time`, `staff`, `shift`, `product_id`, `product_name`, `unit`, `quantity`, `unit_price`, `total_price`, `supplier`, `reason`
        # 因此 SQL 查詢應該是：
        avg_price_query = """
            SELECT AVG(unit_price) 
            FROM transactions 
            WHERE product_name = ? AND unit = ? AND transaction_type = '進貨' 
        """
        params = (product_name, unit)
        result = db_manager.execute_query(avg_price_query, params)

        if result and result[0] and result[0][0] is not None:
            avg_price = float(result[0][0])
            logger.info(f"產品 '{product_name}' ({unit}) 的平均進貨價為: {avg_price}")
            return avg_price
        else:
            logger.warning(f"找不到產品 '{product_name}' ({unit}) 的進貨記錄，無法計算平均進貨價。")
            return None # 或者可以返回一個預設值或查詢當前售價作為備用
    except Exception as e:
        logger.error(f"計算平均進貨價時出錯 for {product_name} ({unit}): {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
