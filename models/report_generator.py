import os
import pandas as pd
import traceback
from models.data_manager import get_inventory
from models.reports import get_monthly_data, get_returns_data
from utils.common import DATA_PATH, REPORTS_PATH, logger

# 生成報表
def generate_reports(year=None, month=None, start_date=None, end_date=None, generate_farmer_details=False, url_for_func=None):
    try:
        # 決定報表目錄名稱和日期範圍描述
        if start_date and end_date:
            date_range_str = f"{start_date} 至 {end_date}"
            report_dir_name = f"{start_date}_to_{end_date}"
        else:
            date_range_str = f"{year}年{month:02d}月"
            report_dir_name = f"{year}年{month:02d}月"
        
        # 讀取所有需要的數據
        sales_df = get_monthly_data('sales.xlsx', year, month, start_date, end_date)
        purchases_df = get_monthly_data('purchases.xlsx', year, month, start_date, end_date)
        returns_df = get_returns_data(year, month, start_date, end_date)
        
        # 讀取員工和小農信息
        staff_farmers_path = os.path.join(DATA_PATH, 'staff_farmers.xlsx')
        
        if not os.path.exists(staff_farmers_path):
            logger.error(f"找不到員工和小農資料: {staff_farmers_path}")
            return False, None, []
        
        staff_farmers_df = pd.read_excel(staff_farmers_path)
        
        # 如果沒有數據，返回 False
        if sales_df.empty and purchases_df.empty and returns_df.empty:
            if start_date and end_date:
                logger.warning(f"找不到 {start_date} 至 {end_date} 的銷售、進貨或退貨數據")
            else:
                logger.warning(f"找不到 {year}年{month}月 的銷售、進貨或退貨數據")
            return False, None, []
        
        # 準備報表目錄
        report_dir = os.path.join(REPORTS_PATH, report_dir_name)
        if not os.path.exists(report_dir):
            os.makedirs(report_dir, exist_ok=True)
        
        # 1. 廠商月報
        farmer_report = pd.DataFrame(columns=['廠商', '總銷售額', '分潤比例', '分潤金額'])
        
        # 獲取所有廠商
        farmers = staff_farmers_df[staff_farmers_df['類型'] == 'farmer']
        
        # 讀取目前庫存
        inventory = get_inventory()
        
        for _, farmer in farmers.iterrows():
            farmer_name = farmer['名稱']
            commission_rate = farmer['分潤比例']
            
            # 獲取庫存中屬於該廠商的產品
            farmer_products = inventory[inventory['供應商'] == farmer_name]['產品名稱'].unique().tolist()
            
            # 計算銷售總額
            total_sales = sales_df[sales_df['產品名稱'].isin(farmer_products)]['總價'].sum()
            commission_amount = total_sales * commission_rate
            
            farmer_report = pd.concat([farmer_report, pd.DataFrame({
                '廠商': [farmer_name],
                '總銷售額': [total_sales],
                '分潤比例': [commission_rate],
                '分潤金額': [commission_amount]
            })], ignore_index=True)
        
        # 2. 員工月報
        staff_report = pd.DataFrame(columns=['員工', '總銷售額', '分潤比例', '分潤金額'])
        
        # 獲取所有員工
        staffs = staff_farmers_df[staff_farmers_df['類型'] == 'staff']
        
        for _, staff in staffs.iterrows():
            staff_name = staff['名稱']
            commission_rate = staff['分潤比例']
            
            # 計算銷售總額
            total_sales = sales_df[sales_df['員工'] == staff_name]['總價'].sum()
            commission_amount = total_sales * commission_rate
            
            staff_report = pd.concat([staff_report, pd.DataFrame({
                '員工': [staff_name],
                '總銷售額': [total_sales],
                '分潤比例': [commission_rate],
                '分潤金額': [commission_amount]
            })], ignore_index=True)
        
        # 3. 收支表月報（移除總進貨成本）
        total_sales = sales_df['總價'].sum()
        staff_commission = staff_report['分潤金額'].sum()
        farmer_commission = farmer_report['分潤金額'].sum()
        net_profit = total_sales - staff_commission - farmer_commission
        
        financial_report = pd.DataFrame({
            '項目': ['總營業額', '員工分潤', '廠商分潤', '淨利潤'],
            '金額': [total_sales, staff_commission, farmer_commission, net_profit]
        })
        
        # 儲存標準月報表
        farmer_report.to_excel(os.path.join(report_dir, '廠商月報.xlsx'), index=False)
        staff_report.to_excel(os.path.join(report_dir, '員工月報.xlsx'), index=False)
        financial_report.to_excel(os.path.join(report_dir, '收支表月報.xlsx'), index=False)
        
        # 4. 為每個廠商生成包含進退貨明細的報表
        farmer_report_with_details = os.path.join(report_dir, '廠商進退貨明細報表.xlsx')
        with pd.ExcelWriter(farmer_report_with_details) as writer:
            # 先寫入廠商分潤總表
            farmer_report.to_excel(writer, sheet_name='廠商分潤總表', index=False)
            
            # 為每個廠商添加進貨明細工作表
            for _, farmer in farmers.iterrows():
                farmer_name = farmer['名稱']
                # 篩選該廠商的進貨記錄
                farmer_purchases = purchases_df[purchases_df['供應商'] == farmer_name]
                
                if not farmer_purchases.empty:
                    # 按照日期升序排序
                    farmer_purchases = farmer_purchases.sort_values(by=['日期', '時間戳記'])
                    # 將進貨明細寫入工作表
                    farmer_purchases.to_excel(writer, sheet_name=f'{farmer_name}進貨明細', index=False)
                else:
                    # 如果沒有進貨記錄，創建空白工作表
                    pd.DataFrame(columns=['日期', '時間戳記', '產品名稱', '單位', '數量', '單價', '總價', '收貨員工'])\
                      .to_excel(writer, sheet_name=f'{farmer_name}進貨明細', index=False)
                
                # 篩選該廠商的退貨記錄
                farmer_returns = returns_df[returns_df['供應商'] == farmer_name]
                
                # 為每個廠商添加退貨明細工作表
                if not farmer_returns.empty:
                    # 按照日期升序排序
                    farmer_returns = farmer_returns.sort_values(by=['日期', '時間戳記'])
                    # 將退貨明細寫入工作表
                    farmer_returns.to_excel(writer, sheet_name=f'{farmer_name}退貨明細', index=False)
                else:
                    # 如果沒有退貨記錄，創建空白工作表
                    pd.DataFrame(columns=['日期', '時間戳記', '供應商', '產品名稱', '單位', '數量', '單價', '總價', '處理員工', '退貨原因'])\
                      .to_excel(writer, sheet_name=f'{farmer_name}退貨明細', index=False)
        
        # 準備報表檔案的下載連結
        report_files = [
            {
                'name': '廠商月報.xlsx',
                'url': url_for_func('main_routes.download_report', path=os.path.join(report_dir_name, '廠商月報.xlsx'))
            },
            {
                'name': '員工月報.xlsx',
                'url': url_for_func('main_routes.download_report', path=os.path.join(report_dir_name, '員工月報.xlsx'))
            },
            {
                'name': '收支表月報.xlsx',
                'url': url_for_func('main_routes.download_report', path=os.path.join(report_dir_name, '收支表月報.xlsx'))
            },
            {
                'name': '廠商進退貨明細報表.xlsx',
                'url': url_for_func('main_routes.download_report', path=os.path.join(report_dir_name, '廠商進退貨明細報表.xlsx'))
            }
        ]
        
        # 如果需要，生成小農詳細報表
        farmer_detail_files = []
        if generate_farmer_details:
            # 為每個廠商生成詳細報表
            farmer_details_dir = os.path.join(report_dir, '廠商詳細報表')
            if not os.path.exists(farmer_details_dir):
                os.makedirs(farmer_details_dir, exist_ok=True)
            
            # 生成廠商詳細報表
            for _, farmer in farmers.iterrows():
                farmer_name = farmer['名稱']
                commission_rate = farmer['分潤比例']
                
                # 獲取庫存中屬於該廠商的產品
                farmer_products = inventory[inventory['供應商'] == farmer_name]['產品名稱'].unique().tolist()
                
                # 篩選該廠商的銷售記錄
                farmer_sales = sales_df[sales_df['產品名稱'].isin(farmer_products)]
                total_sales = farmer_sales['總價'].sum()
                
                # 篩選該廠商的進貨記錄
                farmer_purchases = purchases_df[purchases_df['供應商'] == farmer_name]
                total_purchases = farmer_purchases['總價'].sum()
                
                # 篩選該廠商的退貨記錄
                farmer_returns = returns_df[returns_df['供應商'] == farmer_name]
                total_returns = farmer_returns['總價'].sum() if not farmer_returns.empty else 0
                
                # 計算廠商分潤金額
                commission_amount = total_sales * commission_rate
                
                # 計算庫存價值
                current_inventory = inventory[inventory['供應商'] == farmer_name]
                inventory_value = (current_inventory['數量'] * current_inventory['單價']).sum()
                
                # 創建 Excel 工作簿
                detail_report_path = os.path.join(farmer_details_dir, f"{farmer_name}詳細報表.xlsx")
                with pd.ExcelWriter(detail_report_path) as writer:
                    # 1. 總覽工作表（增加退貨總額信息）
                    summary_df = pd.DataFrame({
                        '項目': ['廠商名稱', '報表期間', '銷售總額', '進貨總額', '退貨總額', '分潤比例', '分潤金額', '庫存價值'],
                        '內容': [farmer_name, date_range_str, total_sales, total_purchases, 
                                total_returns, f"{commission_rate:.2%}", commission_amount, inventory_value]
                    })
                    summary_df.to_excel(writer, sheet_name='總覽', index=False)
                    
                    # 2. 進貨明細表
                    if not farmer_purchases.empty:
                        # 刻意欄位對齊
                        purchases_columns = ['日期', '時間戳記', '產品名稱', '單位', '數量', '單價', '總價', '收貨員工']
                        cols_to_use = [col for col in purchases_columns if col in farmer_purchases.columns]
                        farmer_purchases[cols_to_use].to_excel(writer, sheet_name='進貨明細', index=False)
                    else:
                        # 如果沒有進貨記錄，創建空白工作表
                        pd.DataFrame(columns=['日期', '時間戳記', '產品名稱', '單位', '數量', '單價', '總價', '收貨員工'])\
                          .to_excel(writer, sheet_name='進貨明細', index=False)
                    
                    # 3. 銷售明細表
                    if not farmer_sales.empty:
                        # 刻意欄位對齊
                        sales_columns = ['日期', '時間戳記', '班別', '產品名稱', '單位', '數量', '單價', '總價', '員工']
                        cols_to_use = [col for col in sales_columns if col in farmer_sales.columns]
                        farmer_sales[cols_to_use].to_excel(writer, sheet_name='銷售明細', index=False)
                    else:
                        # 如果沒有銷售記錄，創建空白工作表
                        pd.DataFrame(columns=['日期', '時間戳記', '班別', '產品名稱', '單位', '數量', '單價', '總價', '員工'])\
                          .to_excel(writer, sheet_name='銷售明細', index=False)
                    
                    # 4. 退貨明細表
                    if not farmer_returns.empty:
                        # 按照日期升序排序
                        farmer_returns = farmer_returns.sort_values(by=['日期', '時間戳記'])
                        farmer_returns.to_excel(writer, sheet_name='退貨明細', index=False)
                    else:
                        # 如果沒有退貨記錄，創建空白工作表
                        pd.DataFrame(columns=['日期', '時間戳記', '供應商', '產品名稱', '單位', '數量', '單價', '總價', '處理員工', '退貨原因'])\
                          .to_excel(writer, sheet_name='退貨明細', index=False)
                    
                    # 5. 庫存明細表
                    if not current_inventory.empty:
                        # 計算每個產品的庫存價值
                        inventory_cols = ['產品編號', '產品名稱', '單位', '數量', '單價']
                        cols_to_use = [col for col in inventory_cols if col in current_inventory.columns]
                        inventory_data = current_inventory[cols_to_use].copy()
                        inventory_data['庫存價值'] = current_inventory['數量'] * current_inventory['單價']
                        inventory_data.to_excel(writer, sheet_name='庫存明細', index=False)
                    else:
                        # 如果沒有庫存記錄，創建空白工作表
                        pd.DataFrame(columns=['產品編號', '產品名稱', '單位', '數量', '單價', '庫存價值'])\
                          .to_excel(writer, sheet_name='庫存明細', index=False)
                
                # 記錄報表檔案路徑
                relative_path = os.path.join(report_dir_name, '廠商詳細報表', f"{farmer_name}詳細報表.xlsx")
                farmer_detail_files.append({
                    'name': f"{farmer_name}詳細報表.xlsx",
                    'url': url_for_func('main_routes.download_report', path=relative_path)
                })
            
            # 將廠商詳細報表添加到下載列表
            report_files.extend(farmer_detail_files)
            logger.info(f"生成了 {len(farmer_detail_files)} 個廠商詳細報表")
        
        logger.info(f"報表生成成功，儲存到 {report_dir}")
        return True, report_dir, report_files
    except Exception as e:
        logger.error(f"生成報表時出錯: {str(e)}")
        logger.error(traceback.format_exc())
        return False, None, []
