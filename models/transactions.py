import os
import pandas as pd
from utils.common import get_taiwan_time, logger
from models.data_manager import add_transaction, read_inventory, read_transactions
from models.inventory import update_inventory_quantity, get_product_details
from database import db_manager
from typing import Optional

# 記錄進貨
def record_purchase(date, supplier, product_name, unit, quantity, unit_price, staff):
    try:
        # 計算總價
        total_price = quantity * unit_price
        
        # 獲取台灣時間
        current_time = get_taiwan_time().strftime('%H:%M:%S')
        
        # 檢查產品是否已存在於庫存
        product_info = get_product_details(product_name=product_name)
        
        # 準備交易數據
        transaction_data = {
            '交易類型': '進貨',
            '日期': date,
            '時間': current_time,
            '員工': staff,
            '班別': '',  # 進貨不需要班別
            '產品名稱': product_name,
            '單位': unit,
            '數量': quantity,
            '單價': unit_price,
            '總價': total_price,
            '供應商': supplier,
            '退貨原因': ''  # 進貨不需要退貨原因
        }
        
        # 如果產品已存在，添加產品編號並更新庫存
        if product_info:
            # 查找相同單位的產品
            matching_unit = next((u for u in product_info['units_info'] if u['unit'] == unit), None)
            
            if matching_unit:
                # 產品和單位都匹配，更新數量
                product_id = matching_unit['product_id']
                transaction_data['產品編號'] = product_id
                update_inventory_quantity(product_id, unit, quantity)
            else:
                # 產品存在但單位不同，創建新的產品條目
                from models.inventory import add_new_product
                product_id = add_new_product(product_name, unit, quantity, unit_price, supplier)
                transaction_data['產品編號'] = product_id
        else:
            # 產品不存在，添加到庫存
            from models.inventory import add_new_product
            product_id = add_new_product(product_name, unit, quantity, unit_price, supplier)
            transaction_data['產品編號'] = product_id
        
        # 添加交易記錄
        transaction_id = add_transaction(transaction_data)
        
        logger.info(f"已記錄進貨交易: ID {transaction_id}, 產品 {product_name}, 數量 {quantity} {unit}")
        return transaction_id
    except Exception as e:
        logger.error(f"記錄進貨時出錯: {str(e)}")
        return None

# 記錄銷售
def record_sale(date, shift, staff, product_name, unit, quantity, unit_price):
    try:
        # 獲取產品詳情
        product_info = get_product_details(product_name=product_name)
        
        if not product_info:
            logger.error(f"找不到產品: {product_name}")
            return None
        
        # 查找相同單位的產品
        matching_unit = next((u for u in product_info['units_info'] if u['unit'] == unit), None)
        
        if not matching_unit:
            logger.error(f"找不到產品單位: {product_name}, {unit}")
            return None
        
        # 檢查庫存是否足夠
        if matching_unit['quantity'] < quantity:
            logger.error(f"庫存不足: {product_name}, {unit}, 需要 {quantity}, 庫存 {matching_unit['quantity']}")
            return None
        
        # 計算總價
        total_price = quantity * unit_price
        
        # 獲取台灣時間
        current_time = get_taiwan_time().strftime('%H:%M:%S')
        
        # 準備交易數據
        transaction_data = {
            '交易類型': '銷售',
            '日期': date,
            '時間': current_time,
            '員工': staff,
            '班別': shift,
            '產品編號': matching_unit['product_id'],
            '產品名稱': product_name,
            '單位': unit,
            '數量': quantity,
            '單價': unit_price,
            '總價': total_price,
            '供應商': matching_unit['supplier'],
            '退貨原因': ''  # 銷售不需要退貨原因
        }
        
        # 添加交易記錄
        transaction_id = add_transaction(transaction_data)
        
        # 更新庫存（減少庫存數量）
        update_inventory_quantity(matching_unit['product_id'], unit, -quantity)
        
        logger.info(f"已記錄銷售交易: ID {transaction_id}, 產品 {product_name}, 數量 {quantity} {unit}")
        return transaction_id
    except Exception as e:
        logger.error(f"記錄銷售時出錯: {str(e)}")
        return None

# 記錄退貨
def record_return(date, supplier, product_name, unit, quantity, staff, reason):
    try:
        # 獲取產品詳情
        product_info = get_product_details(product_name=product_name)
        
        if not product_info:
            logger.error(f"找不到產品: {product_name}")
            return None
        
        # 查找相同單位的產品
        matching_unit = next((u for u in product_info['units_info'] if u['unit'] == unit and u['supplier'] == supplier), None)
        
        if not matching_unit:
            logger.error(f"找不到產品單位或供應商不匹配: {product_name}, {unit}, {supplier}")
            return None
        
        # 檢查庫存是否足夠
        if matching_unit['quantity'] < quantity:
            logger.error(f"庫存不足，無法退貨: {product_name}, {unit}, 需要 {quantity}, 庫存 {matching_unit['quantity']}")
            return None
        
        # 單價和總價
        unit_price = matching_unit['unit_price']
        total_price = quantity * unit_price
        
        # 獲取台灣時間
        current_time = get_taiwan_time().strftime('%H:%M:%S')
        
        # 準備交易數據
        transaction_data = {
            '交易類型': '退貨',
            '日期': date,
            '時間': current_time,
            '員工': staff,
            '班別': '',  # 退貨不需要班別
            '產品編號': matching_unit['product_id'],
            '產品名稱': product_name,
            '單位': unit,
            '數量': quantity,
            '單價': unit_price,
            '總價': total_price,
            '供應商': supplier,
            '退貨原因': reason
        }
        
        # 添加交易記錄
        transaction_id = add_transaction(transaction_data)
        
        # 更新庫存（減少庫存數量）
        update_inventory_quantity(matching_unit['product_id'], unit, -quantity)
        
        logger.info(f"已記錄退貨交易: ID {transaction_id}, 產品 {product_name}, 數量 {quantity} {unit}")
        return transaction_id
    except Exception as e:
        logger.error(f"記錄退貨時出錯: {str(e)}")
        return None

def record_sales_return(original_transaction_id: str, staff: str, reason: str = "") -> Optional[str]:
    """
    根據原始銷售交易ID記錄一筆銷售退貨交易。
    銷退會增加庫存。
    總價會是負数。
    """
    try:
        # 1. 根據 original_transaction_id 讀取原始銷售記錄
        # 假設 read_transactions 返回的 DataFrame 欄位名是中文的
        # 並且可以通過交易ID查詢單筆記錄 (需要確認 read_transactions 是否支持，或直接用 db_manager)
        
        # 直接使用 db_manager.execute_query 獲取原始交易數據
        query = """
            SELECT transaction_id, transaction_type, date, time, staff, shift, 
                   product_id, product_name, unit, quantity, unit_price, total_price, supplier, return_reason
            FROM transactions
            WHERE transaction_id = ? AND transaction_type = '銷售'
        """
        params = (original_transaction_id,)
        original_sale_list = db_manager.execute_query(query, params)

        if not original_sale_list:
            logger.error(f"[銷退] 找不到原始銷售記錄 ID: {original_transaction_id}")
            return None
        
        original_sale = original_sale_list[0] # 獲取第一條 (也是唯一一條) 記錄
        
        # 從元組轉換為字典，方便取值 (假設欄位順序與SELECT語句一致)
        columns = ['交易ID', '交易類型', '日期', '時間', '員工', '班別', '產品編號', '產品名稱', '單位', '數量', '單價', '總價', '供應商', '退貨原因']
        original_sale_data = dict(zip(columns, original_sale))

        # 獲取銷退的相關信息
        current_time_simple = get_taiwan_time().strftime('%H:%M:%S')
        # 退貨的日期應為當前日期，而不是原始銷售日期
        current_date = get_taiwan_time().strftime('%Y-%m-%d') 

        # 準備銷退交易數據
        sales_return_data = {
            '交易類型': '銷退',
            '日期': current_date, # 使用當前日期進行銷退
            '時間': current_time_simple,
            '員工': staff, # 處理退貨的員工
            '班別': original_sale_data['班別'], # 可以沿用原銷售班別，或設為當前班別
            '產品編號': original_sale_data['產品編號'],
            '產品名稱': original_sale_data['產品名稱'],
            '單位': original_sale_data['單位'],
            '數量': original_sale_data['數量'], # 退貨數量與原銷售數量一致
            '單價': original_sale_data['單價'], # 退貨單價與原銷售單價一致
            '總價': -abs(float(original_sale_data['總價'])), # 總價為原銷售總價的負值
            '供應商': original_sale_data['供應商'],
            '退貨原因': reason,
            '原始交易ID': original_transaction_id # 新增欄位記錄原始銷售ID，便於追蹤
        }

        # 2. 添加銷退交易記錄
        # 注意：add_transaction 可能需要調整以接受 '原始交易ID' 這個新欄位，
        # 或者將其存儲在 '退貨原因' 或其他現有欄位中 (例如: f"{reason} (原單號: {original_transaction_id})")
        # 為了保持 transactions 表結構穩定，暫時不直接添加新欄位到 transactions 表，
        # 而是將原始交易ID信息放入退貨原因。
        # 如果 transactions 表可以修改，則 add_transaction 和表結構都需要更新。
        
        # 決定如何處理 original_transaction_id 的存儲
        # 方案 A: 修改 transactions 表和 add_transaction，增加 original_transaction_id 欄位 (較佳)
        # 方案 B: 存入退貨原因 (臨時方案)
        # 此處先假設採用方案 A，但 add_transaction 需要同步修改
        # 由於不能修改 add_transaction，我們將原始ID放入原因
        if reason:
            sales_return_data['退貨原因'] = f"{reason} (原始單號: {original_transaction_id})"
        else:
            sales_return_data['退貨原因'] = f"原始單號: {original_transaction_id}"


        # 移除 '原始交易ID'，因為目前 add_transaction 不支持
        if '原始交易ID' in sales_return_data:
            del sales_return_data['原始交易ID']

        new_transaction_id = add_transaction(sales_return_data)
        if not new_transaction_id:
            logger.error(f"[銷退] 新增銷退交易記錄失敗 for original ID: {original_transaction_id}")
            return None

        # 3. 更新庫存 (增加庫存數量)
        update_success = update_inventory_quantity(
            product_id=original_sale_data['產品編號'], 
            unit=original_sale_data['單位'], 
            quantity_change=float(original_sale_data['數量']) # 加回庫存，所以是正數
        )
        
        if not update_success:
            logger.error(f"[銷退] 更新庫存失敗 for product ID: {original_sale_data['產品編號']}, unit: {original_sale_data['單位']}")
            # 此處可以考慮是否需要回滾銷退交易記錄，取決於業務需求
            # 暫時只記錄錯誤

        logger.info(f"已記錄銷貨退回: 新交易ID {new_transaction_id} (對應原銷售ID {original_transaction_id}), 產品 {original_sale_data['產品名稱']}")
        return new_transaction_id

    except Exception as e:
        logger.error(f"記錄銷貨退回 (基於原始交易ID {original_transaction_id}) 時發生錯誤: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
