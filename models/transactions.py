import os
import pandas as pd
from utils.common import get_taiwan_time, logger
from models.data_manager import add_transaction, read_inventory
from models.inventory import update_inventory_quantity, get_product_details

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
