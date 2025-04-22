"""
雲端報表生成器模組 for GAS_STATION_POS_v2
整合 Google Drive 雲端儲存功能的報表生成器
"""
import os
import pandas as pd
from datetime import datetime
from utils.common import REPORTS_PATH, logger
from utils.cloud.google_drive_connector import GoogleDriveConnector
from utils.cloud.cloud_config_manager import CloudConfigManager
from models.cloud_data_manager import read_master_data, read_transactions, read_inventory

# 雲端配置管理器
cloud_config = CloudConfigManager()
drive_connector = GoogleDriveConnector(
    credentials_path=cloud_config.get("credentials_path"),
    token_path=cloud_config.get("token_path")
)

# 生成基本報表（銷售額、廠商分潤、員工分潤）
def generate_basic_reports(year=None, month=None, start_date=None, end_date=None):
    """
    生成基本報表並保存到雲端或本地
    
    參數:
        year (int, optional): 年份
        month (int, optional): 月份
        start_date (str, optional): 開始日期
        end_date (str, optional): 結束日期
    
    返回:
        tuple: (是否成功, 報表目錄, 報表文件列表)
    """
    try:
        # 決定報表目錄名稱和日期範圍描述
        if start_date and end_date:
            date_range_str = f"{start_date}_to_{end_date}"
            report_dir_name = f"{start_date}_to_{end_date}"
        else:
            date_range_str = f"{year}年{month:02d}月"
            report_dir_name = f"{year}年{month:02d}月"
        
        # 準備本地報表目錄
        local_report_dir = os.path.join(REPORTS_PATH, report_dir_name)
        if not os.path.exists(local_report_dir):
            os.makedirs(local_report_dir, exist_ok=True)
        
        # 雲端報表路徑
        cloud_report_dir = f"reports/{report_dir_name}"
        
        # 讀取交易記錄
        sales_df = read_transactions('銷售', start_date, end_date)
        purchases_df = read_transactions('進貨', start_date, end_date)
        returns_df = read_transactions('退貨', start_date, end_date)
        
        # 讀取當前庫存
        inventory_df = read_inventory()
        
        # 讀取員工和廠商資料
        staff_farmers_df = read_master_data('員工廠商')
        
        # 如果沒有銷售數據，返回 False
        if sales_df.empty and purchases_df.empty and returns_df.empty:
            logger.warning(f"找不到指定期間的交易數據: {date_range_str}")
            return False, None, []
        
        # 1. 廠商月報
        farmer_report = pd.DataFrame(columns=['廠商', '總銷售額', '分潤比例', '分潤金額'])
        
        # 獲取所有廠商
        farmers = staff_farmers_df[staff_farmers_df['類型'] == 'farmer']
        
        for _, farmer in farmers.iterrows():
            farmer_name = farmer['名稱']
            commission_rate = farmer['分潤比例']
            
            # 獲取屬於該廠商的產品銷售記錄
            farmer_sales = sales_df[sales_df['供應商'] == farmer_name]
            total_sales = farmer_sales['總價'].sum() if not farmer_sales.empty else 0
            commission_amount = total_sales * commission_rate
            
            # 添加到報表
            new_row = pd.DataFrame({
                '廠商': [farmer_name],
                '總銷售額': [total_sales],
                '分潤比例': [commission_rate],
                '分潤金額': [commission_amount]
            })
            farmer_report = pd.concat([farmer_report, new_row], ignore_index=True)
        
        # 2. 員工月報
        staff_report = pd.DataFrame(columns=['員工', '總銷售額', '分潤比例', '分潤金額'])
        
        # 獲取所有員工
        staffs = staff_farmers_df[staff_farmers_df['類型'] == 'staff']
        
        for _, staff in staffs.iterrows():
            staff_name = staff['名稱']
            commission_rate = staff['分潤比例']
            
            # 計算銷售總額
            staff_sales = sales_df[sales_df['員工'] == staff_name]
            total_sales = staff_sales['總價'].sum() if not staff_sales.empty else 0
            commission_amount = total_sales * commission_rate
            
            # 添加到報表
            new_row = pd.DataFrame({
                '員工': [staff_name],
                '總銷售額': [total_sales],
                '分潤比例': [commission_rate],
                '分潤金額': [commission_amount]
            })
            staff_report = pd.concat([staff_report, new_row], ignore_index=True)
        
        # 3. 收支表月報
        total_sales = sales_df['總價'].sum() if not sales_df.empty else 0
        total_purchases = purchases_df['總價'].sum() if not purchases_df.empty else 0
        total_returns = returns_df['總價'].sum() if not returns_df.empty else 0
        staff_commission = staff_report['分潤金額'].sum()
        farmer_commission = farmer_report['分潤金額'].sum()
        net_profit = total_sales - staff_commission - farmer_commission
        
        financial_report = pd.DataFrame({
            '項目': ['總營業額', '進貨成本', '退貨金額', '員工分潤', '廠商分潤', '淨利潤'],
            '金額': [total_sales, total_purchases, total_returns, staff_commission, farmer_commission, net_profit]
        })
        
        # 報表檔案名稱和路徑
        farmer_report_name = '廠商月報.xlsx'
        staff_report_name = '員工月報.xlsx'
        financial_report_name = '收支表月報.xlsx'
        
        # 本地報表路徑
        local_farmer_report_path = os.path.join(local_report_dir, farmer_report_name)
        local_staff_report_path = os.path.join(local_report_dir, staff_report_name)
        local_financial_report_path = os.path.join(local_report_dir, financial_report_name)
        
        # 保存報表到本地
        farmer_report.to_excel(local_farmer_report_path, index=False)
        staff_report.to_excel(local_staff_report_path, index=False)
        financial_report.to_excel(local_financial_report_path, index=False)
        
        # 如果啟用雲端模式，也保存到雲端
        share_links = {}
        if cloud_config.is_cloud_mode():
            # 確保雲端報表目錄存在
            drive_connector.ensure_directory(cloud_report_dir)
            
            # 上傳報表到雲端
            cloud_farmer_report_path = f"{cloud_report_dir}/{farmer_report_name}"
            cloud_staff_report_path = f"{cloud_report_dir}/{staff_report_name}"
            cloud_financial_report_path = f"{cloud_report_dir}/{financial_report_name}"
            
            # 上傳並創建分享連結
            farmer_file_id = drive_connector.upload_file(local_farmer_report_path, cloud_report_dir, farmer_report_name)
            staff_file_id = drive_connector.upload_file(local_staff_report_path, cloud_report_dir, staff_report_name)
            financial_file_id = drive_connector.upload_file(local_financial_report_path, cloud_report_dir, financial_report_name)
            
            if farmer_file_id:
                share_links[farmer_report_name] = drive_connector.create_share_link(farmer_file_id)
            
            if staff_file_id:
                share_links[staff_report_name] = drive_connector.create_share_link(staff_file_id)
            
            if financial_file_id:
                share_links[financial_report_name] = drive_connector.create_share_link(financial_file_id)
        
        # 返回報表路徑和報表文件列表
        report_files = [
            {
                'name': farmer_report_name, 
                'path': local_farmer_report_path,
                'share_link': share_links.get(farmer_report_name)
            },
            {
                'name': staff_report_name, 
                'path': local_staff_report_path,
                'share_link': share_links.get(staff_report_name)
            },
            {
                'name': financial_report_name, 
                'path': local_financial_report_path,
                'share_link': share_links.get(financial_report_name)
            }
        ]
        
        logger.info(f"基本報表生成成功，保存在: {local_report_dir}")
        if cloud_config.is_cloud_mode():
            logger.info(f"報表已同步到雲端: {cloud_report_dir}")
        
        return True, local_report_dir, report_files
    except Exception as e:
        logger.error(f"生成基本報表時出錯: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None, []

# 生成廠商詳細報表
def generate_farmer_detailed_reports(year=None, month=None, start_date=None, end_date=None):
    """
    生成廠商詳細報表並保存到雲端或本地
    
    參數:
        year (int, optional): 年份
        month (int, optional): 月份
        start_date (str, optional): 開始日期
        end_date (str, optional): 結束日期
    
    返回:
        tuple: (是否成功, 報表目錄, 報表文件列表)
    """
    try:
        # 決定報表目錄名稱和日期範圍描述
        if start_date and end_date:
            date_range_str = f"{start_date} 至 {end_date}"
            report_dir_name = f"{start_date}_to_{end_date}"
        else:
            date_range_str = f"{year}年{month:02d}月"
            report_dir_name = f"{year}年{month:02d}月"
        
        # 準備本地報表目錄
        local_report_dir = os.path.join(REPORTS_PATH, report_dir_name, '廠商詳細報表')
        if not os.path.exists(local_report_dir):
            os.makedirs(local_report_dir, exist_ok=True)
        
        # 雲端報表路徑
        cloud_report_dir = f"reports/{report_dir_name}/廠商詳細報表"
        
        # 讀取交易記錄
        sales_df = read_transactions('銷售', start_date, end_date)
        purchases_df = read_transactions('進貨', start_date, end_date)
        returns_df = read_transactions('退貨', start_date, end_date)
        
        # 讀取當前庫存
        inventory_df = read_inventory()
        
        # 讀取員工和廠商資料
        staff_farmers_df = read_master_data('員工廠商')
        
        # 獲取所有廠商
        farmers = staff_farmers_df[staff_farmers_df['類型'] == 'farmer']
        
        report_files = []
        share_links = {}
        
        # 確保雲端報表目錄存在（如果啟用了雲端模式）
        if cloud_config.is_cloud_mode():
            drive_connector.ensure_directory(cloud_report_dir)
        
        # 為每個廠商生成詳細報表
        for _, farmer in farmers.iterrows():
            farmer_name = farmer['名稱']
            commission_rate = farmer['分潤比例']
            
            # 篩選該廠商的銷售記錄
            farmer_sales = sales_df[sales_df['供應商'] == farmer_name]
            total_sales = farmer_sales['總價'].sum() if not farmer_sales.empty else 0
            
            # 篩選該廠商的進貨記錄
            farmer_purchases = purchases_df[purchases_df['供應商'] == farmer_name]
            total_purchases = farmer_purchases['總價'].sum() if not farmer_purchases.empty else 0
            
            # 篩選該廠商的退貨記錄
            farmer_returns = returns_df[returns_df['供應商'] == farmer_name]
            total_returns = farmer_returns['總價'].sum() if not farmer_returns.empty else 0
            
            # 計算廠商分潤金額
            commission_amount = total_sales * commission_rate
            
            # 計算庫存價值
            current_inventory = inventory_df[inventory_df['供應商'] == farmer_name]
            inventory_value = (current_inventory['數量'] * current_inventory['單價']).sum() if not current_inventory.empty else 0
            
            # 報表檔案名稱
            report_name = f"{farmer_name}詳細報表.xlsx"
            local_report_path = os.path.join(local_report_dir, report_name)
            
            # 創建 Excel 工作簿
            with pd.ExcelWriter(local_report_path) as writer:
                # 1. 總覽工作表
                summary_df = pd.DataFrame({
                    '項目': ['廠商名稱', '報表期間', '銷售總額', '進貨總額', '退貨總額', '分潤比例', '分潤金額', '庫存價值'],
                    '內容': [farmer_name, date_range_str, total_sales, total_purchases, 
                            total_returns, f"{commission_rate:.2%}", commission_amount, inventory_value]
                })
                summary_df.to_excel(writer, sheet_name='總覽', index=False)
                
                # 2. 進貨明細表
                if not farmer_purchases.empty:
                    # 只保留需要的列
                    columns_to_keep = ['日期', '時間', '產品名稱', '單位', '數量', '單價', '總價', '員工']
                    columns_to_keep = [col for col in columns_to_keep if col in farmer_purchases.columns]
                    farmer_purchases[columns_to_keep].to_excel(writer, sheet_name='進貨明細', index=False)
                else:
                    # 如果沒有進貨記錄，創建空白工作表
                    pd.DataFrame(columns=['日期', '時間', '產品名稱', '單位', '數量', '單價', '總價', '員工'])\
                      .to_excel(writer, sheet_name='進貨明細', index=False)
                
                # 3. 銷售明細表
                if not farmer_sales.empty:
                    # 只保留需要的列
                    columns_to_keep = ['日期', '時間', '班別', '產品名稱', '單位', '數量', '單價', '總價', '員工']
                    columns_to_keep = [col for col in columns_to_keep if col in farmer_sales.columns]
                    farmer_sales[columns_to_keep].to_excel(writer, sheet_name='銷售明細', index=False)
                else:
                    # 如果沒有銷售記錄，創建空白工作表
                    pd.DataFrame(columns=['日期', '時間', '班別', '產品名稱', '單位', '數量', '單價', '總價', '員工'])\
                      .to_excel(writer, sheet_name='銷售明細', index=False)
                
                # 4. 退貨明細表
                if not farmer_returns.empty:
                    # 只保留需要的列
                    columns_to_keep = ['日期', '時間', '產品名稱', '單位', '數量', '單價', '總價', '員工', '退貨原因']
                    columns_to_keep = [col for col in columns_to_keep if col in farmer_returns.columns]
                    farmer_returns[columns_to_keep].to_excel(writer, sheet_name='退貨明細', index=False)
                else:
                    # 如果沒有退貨記錄，創建空白工作表
                    pd.DataFrame(columns=['日期', '時間', '產品名稱', '單位', '數量', '單價', '總價', '員工', '退貨原因'])\
                      .to_excel(writer, sheet_name='退貨明細', index=False)
                
                # 5. 庫存明細表
                if not current_inventory.empty:
                    # 計算每個產品的庫存價值
                    inventory_data = current_inventory.copy()
                    inventory_data['庫存價值'] = inventory_data['數量'] * inventory_data['單價']
                    inventory_data.to_excel(writer, sheet_name='庫存明細', index=False)
                else:
                    # 如果沒有庫存記錄，創建空白工作表
                    pd.DataFrame(columns=['產品編號', '產品名稱', '單位', '數量', '單價', '供應商', '庫存價值'])\
                      .to_excel(writer, sheet_name='庫存明細', index=False)
            
            # 如果啟用雲端模式，將報表上傳到雲端
            if cloud_config.is_cloud_mode():
                file_id = drive_connector.upload_file(local_report_path, cloud_report_dir, report_name)
                if file_id:
                    share_links[report_name] = drive_connector.create_share_link(file_id)
            
            # 添加到報表文件列表
            report_files.append({
                'name': report_name,
                'path': local_report_path,
                'share_link': share_links.get(report_name)
            })
        
        logger.info(f"廠商詳細報表生成成功，共 {len(report_files)} 個報表，保存在: {local_report_dir}")
        if cloud_config.is_cloud_mode():
            logger.info(f"報表已同步到雲端: {cloud_report_dir}")
        
        return True, local_report_dir, report_files
    except Exception as e:
        logger.error(f"生成廠商詳細報表時出錯: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None, []

# 統一報表生成入口
def generate_reports(year=None, month=None, start_date=None, end_date=None, generate_farmer_details=False):
    """
    統一報表生成入口，生成所有報表並保存到雲端或本地
    
    參數:
        year (int, optional): 年份
        month (int, optional): 月份
        start_date (str, optional): 開始日期
        end_date (str, optional): 結束日期
        generate_farmer_details (bool, optional): 是否生成廠商詳細報表
    
    返回:
        tuple: (是否成功, 報表目錄, 報表文件列表)
    """
    # 生成基本報表
    basic_success, basic_dir, basic_files = generate_basic_reports(year, month, start_date, end_date)
    
    # 如果基本報表生成失敗，直接返回
    if not basic_success:
        return False, None, []
    
    all_files = basic_files
    
    # 如果需要，生成廠商詳細報表
    if generate_farmer_details:
        farmer_success, farmer_dir, farmer_files = generate_farmer_detailed_reports(year, month, start_date, end_date)
        if farmer_success:
            all_files.extend(farmer_files)
    
    return True, basic_dir, all_files
