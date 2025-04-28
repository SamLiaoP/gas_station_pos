from flask import render_template, request, redirect, url_for, jsonify, Blueprint, send_file, session, flash
from utils.common import get_taiwan_time, logger, get_current_shift
from models.data_manager import get_staff_and_farmers, read_inventory, add_new_farmer, read_master_data, save_master_data
from models.inventory import get_product_details, get_products_by_supplier
from models.transactions import record_purchase, record_sale, record_return
from models.report_generator import generate_reports
from flask_login import login_required, current_user
from auth import authorized_required
import pandas as pd
import os
from datetime import datetime

main_routes = Blueprint('main_routes', __name__)

# 主頁路由
@main_routes.route('/index')
@login_required
@authorized_required
def index():
    today = get_taiwan_time().strftime('%Y-%m-%d')
    current_shift = get_current_shift()
    logger.info(f"訪問首頁，日期：{today}，班別：{current_shift}")
    return render_template('index.html', today=today, current_shift=current_shift)

# 選擇操作頁面
@main_routes.route('/select_operation')
@login_required
@authorized_required
def select_operation():
    logger.info("訪問選擇操作頁面")
    return render_template('select_operation.html')

# 進貨頁面
@main_routes.route('/purchase', methods=['GET', 'POST'])
@login_required
@authorized_required
def purchase():
    if request.method == 'POST':
        # 從表單提交中提取數據
        date = request.form.get('date')
        is_new_supplier = request.form.get('is_new_supplier') == 'true'
        
        if is_new_supplier:
            # 新增廠商
            new_supplier = request.form.get('new_supplier')
            if not new_supplier:
                logger.error("新廠商名稱為空")
                return "請輸入廠商名稱", 400
                
            # 新增廠商到資料庫，預設分潤比例為0.5
            success = add_new_farmer(new_supplier, 0.5)
            
            if not success:
                logger.error(f"新增廠商 '{new_supplier}' 失敗")
                return f"新增廠商 '{new_supplier}' 失敗", 500
                
            logger.info(f"成功新增廠商 '{new_supplier}'")
            supplier = new_supplier
        else:
            # 使用既有廠商
            supplier = request.form.get('supplier')
            
            # 如果選擇的是「新增廠商」選項但沒有啟動新增邏輯，則報錯
            if supplier == '新增廠商':
                logger.error("選擇了新增廠商但沒有提供廠商名稱")
                return "請輸入新廠商名稱或選擇既有廠商", 400
        
        product_name = request.form.get('product_name')
        unit = request.form.get('unit')
        quantity = float(request.form.get('quantity'))
        unit_price = float(request.form.get('unit_price'))
        staff = request.form.get('staff')
        
        logger.info(f"進貨記錄：日期={date}, 供應商={supplier}, 產品={product_name}, 單位={unit}, 數量={quantity}, 單價={unit_price}, 員工={staff}")
        
        try:
            transaction_id = record_purchase(date, supplier, product_name, unit, quantity, unit_price, staff)
            
            if transaction_id:
                logger.info("進貨記錄成功")
                return redirect(url_for('main_routes.select_operation'))
            else:
                logger.error("進貨記錄失敗")
                return "進貨記錄失敗", 500
        except Exception as e:
            logger.error(f"進貨記錄發生錯誤: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return f"進貨記錄發生錯誤: {str(e)}", 500
    
    # 讀取員工和廠商列表
    staff, suppliers = get_staff_and_farmers()
    logger.info(f"訪問進貨頁面，加載員工列表{staff}和廠商列表{suppliers}")
    return render_template('purchase.html', staff=staff, suppliers=suppliers)

# 退貨頁面
@main_routes.route('/return_goods', methods=['GET', 'POST'])
@login_required
@authorized_required
def return_goods():
    if request.method == 'POST':
        # 從表單提交中提取數據
        date = request.form.get('date')
        supplier = request.form.get('supplier')
        product_name = request.form.get('product_name')
        unit = request.form.get('unit')
        quantity = float(request.form.get('quantity'))
        staff = request.form.get('staff')
        reason = request.form.get('reason', '')
        
        logger.info(f"退貨記錄：日期={date}, 廠商={supplier}, 產品={product_name}, 單位={unit}, 數量={quantity}, 員工={staff}, 原因={reason}")
        
        try:
            transaction_id = record_return(date, supplier, product_name, unit, quantity, staff, reason)
            
            if transaction_id:
                logger.info("退貨記錄成功")
                return redirect(url_for('main_routes.select_operation'))
            else:
                logger.error("退貨記錄失敗")
                return "退貨記錄失敗", 500
        except Exception as e:
            logger.error(f"退貨記錄發生錯誤: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return f"退貨記錄發生錯誤: {str(e)}", 500
    
    # 讀取員工和廠商列表
    staff, suppliers = get_staff_and_farmers()
    
    # 為每個廠商讀取產品列表
    products_by_supplier = {}
    for supplier in suppliers:
        products = get_products_by_supplier(supplier)
        if products:
            products_by_supplier[supplier] = products
    
    logger.info(f"訪問退貨頁面，加載員工列表{staff}和廠商清單")
    return render_template('return_goods.html', staff=staff, suppliers=suppliers, products_by_supplier=products_by_supplier)

# 銷售頁面
@main_routes.route('/sale', methods=['GET', 'POST'])
@login_required
@authorized_required
def sale():
    if request.method == 'POST':
        # 從表單提交中提取數據
        date = request.form.get('date')
        shift = request.form.get('shift')
        staff = request.form.get('staff')
        product_name = request.form.get('product_name')
        unit = request.form.get('unit')
        quantity = float(request.form.get('quantity'))
        unit_price = float(request.form.get('unit_price'))
        
        logger.info(f"銷售記錄：日期={date}, 班別={shift}, 員工={staff}, 產品={product_name}, 單位={unit}, 數量={quantity}, 單價={unit_price}")
        
        try:
            transaction_id = record_sale(date, shift, staff, product_name, unit, quantity, unit_price)
            
            if transaction_id:
                logger.info("銷售記錄成功")
                return redirect(url_for('main_routes.select_operation'))
            else:
                logger.error("銷售記錄失敗")
                return "銷售記錄失敗", 500
        except Exception as e:
            logger.error(f"銷售記錄發生錯誤: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return f"銷售記錄發生錯誤: {str(e)}", 500
    
    staff, _ = get_staff_and_farmers()
    inventory = read_inventory()
    # 取得有庫存的產品列表（確保產品名稱不重複）
    products = inventory[inventory['數量'] > 0]['產品名稱'].unique().tolist()
    
    logger.info(f"訪問銷售頁面，加載員工列表{staff}和產品列表{products}")
    return render_template('sale.html', staff=staff, products=products)

# 班別銷售查詢頁面
@main_routes.route('/shift_sales', methods=['GET', 'POST'])
@login_required
@authorized_required
def shift_sales():
    from models.data_manager import read_transactions
    
    today = get_taiwan_time().strftime('%Y-%m-%d')
    current_shift = get_current_shift()
    
    # 準備班別選項
    shifts = ['早班', '午班', '晚班']
    
    # 初始化銷售數據
    sales_data = None
    total_sales_amount = 0
    date = today
    shift = current_shift
    
    if request.method == 'POST':
        # 獲取選擇的日期和班別
        date = request.form.get('date')
        shift = request.form.get('shift')
        
        # 讀取銷售數據
        sales_df = read_transactions('銷售')
        
        # 過濾指定日期和班別的數據
        sales_data = sales_df[(sales_df['日期'] == date) & (sales_df['班別'] == shift)]
        
        # 計算總銷售額
        total_sales_amount = sales_data['總價'].sum() if not sales_data.empty else 0
        
        logger.info(f"查詢班別銷售：日期={date}, 班別={shift}, 找到 {len(sales_data)} 筆記錄")
    
    # 將 DataFrame 轉換為可以在模板中使用的列表
    sales_records = [] if sales_data is None or sales_data.empty else sales_data.to_dict('records')
    
    return render_template('shift_sales.html', 
                           date=date, 
                           shift=shift, 
                           shifts=shifts, 
                           sales_records=sales_records, 
                           total_sales_amount=total_sales_amount)

# API路由：取得產品詳情
@main_routes.route('/api/product_details/<product_name>')
@login_required
@authorized_required
def api_product_details(product_name):
    try:
        # 打印診斷信息
        logger.info(f"API請求產品詳情：'{product_name}'")
        
        details = get_product_details(product_name=product_name)
        if details:
            # 確保回傳結果包含所有必要的資訊
            if 'units' not in details or not details['units']:
                logger.error(f"產品 '{product_name}' 的 units 列表為空或不存在")
                return jsonify({"error": "產品單位資料不完整"}), 500
                
            logger.info(f"回傳 API 結果: 找到 {len(details['units'])} 種單位")
            
            # 特別設置正確的 Content-Type 以確保中文正確顯示
            response = jsonify(details)
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        else:
            logger.warning(f"找不到產品：'{product_name}'")
            return jsonify({"error": "找不到產品"}), 404
    except Exception as e:
        logger.error(f"獲取產品詳情時發生錯誤: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": f"發生錯誤: {str(e)}"}), 500

# API路由：取得廠商產品列表
@main_routes.route('/api/supplier_products/<supplier_name>')
@login_required
@authorized_required
def api_supplier_products(supplier_name):
    try:
        # 打印診斷信息
        logger.info(f"API請求廠商產品：'{supplier_name}'")
        
        # 獲取廠商產品
        products = get_products_by_supplier(supplier_name)
        
        if not products:
            logger.warning(f"找不到廠商 '{supplier_name}' 的庫存產品")
            return jsonify({"error": "找不到廠商庫存"}), 404
            
        logger.info(f"回傳 API 結果: 找到 {len(products)} 個產品")
        
        # 特別設置正確的 Content-Type 以確保中文正確顯示
        response = jsonify({"products": products})
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        logger.error(f"獲取廠商產品時發生錯誤: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": f"發生錯誤: {str(e)}"}), 500

# API路由：取得庫存數據
@main_routes.route('/api/inventory')
@login_required
@authorized_required
def api_inventory():
    logger.info("訪問庫存API")
    inventory_data = read_inventory()
    return jsonify(inventory_data.to_dict('records'))

# 庫存頁面
@main_routes.route('/inventory')
@login_required
@authorized_required
def inventory():
    logger.info("訪問庫存頁面")
    inventory_data = read_inventory()
    logger.info(f"庫存數據計數：{len(inventory_data)}")
    return render_template('inventory.html', inventory=inventory_data.to_dict('records'))

# 下載報表檔案
@main_routes.route('/download_report/<path:path>')
@login_required
@authorized_required
def download_report(path):
    from utils.common import REPORTS_PATH
    import os
    
    report_path = os.path.join(REPORTS_PATH, path)
    
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True)
    else:
        return f"找不到報表文件: {path}", 404

# 報表生成頁面
@main_routes.route('/generate_reports', methods=['GET', 'POST'])
@login_required
@authorized_required
def generate_reports_route():
    if request.method == 'POST':
        # 從表單提取報表參數
        report_type = request.form.get('report_type')
        generate_farmer_details = request.form.get('generate_farmer_details') == 'on'
        
        # 決定日期範圍
        if report_type == 'monthly':
            year = int(request.form.get('year'))
            month = int(request.form.get('month'))
            start_date = None
            end_date = None
            date_range_str = f"{year}年{month}月"
        else:  # custom date range
            year = None
            month = None
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            date_range_str = f"{start_date} 至 {end_date}"
        
        logger.info(f"開始生成報表：{date_range_str}，包含廠商詳細報表: {generate_farmer_details}")
        
        # 生成報表
        success, report_dir, report_files = generate_reports(
            year=year, 
            month=month, 
            start_date=start_date, 
            end_date=end_date, 
            generate_farmer_details=generate_farmer_details
        )
        
        if success:
            logger.info(f"報表生成成功，儲存於：{report_dir}")
            
            # 添加下載URL
            for report in report_files:
                file_name = os.path.basename(report['path'])
                dir_name = os.path.basename(os.path.dirname(report['path']))
                if dir_name == 'reports':
                    # 報表直接在報表根目錄下
                    report['url'] = url_for('main_routes.download_report', path=file_name)
                else:
                    # 報表在子目錄中
                    sub_path = os.path.join(dir_name, file_name)
                    report['url'] = url_for('main_routes.download_report', path=sub_path)
            
            # 返回 JSON 響應，包含成功消息和下載連結
            return jsonify({
                'success': True,
                'message': f"報表已生成完成，檢視期間: {date_range_str}",
                'files': report_files
            })
        else:
            logger.error(f"生成報表失敗")
            return jsonify({
                'success': False,
                'message': "生成報表失敗"
            }), 500
    
    current_year = get_taiwan_time().year
    current_month = get_taiwan_time().month
    
    years = list(range(current_year - 5, current_year + 1))
    months = list(range(1, 13))
    
    logger.info("訪問報表生成頁面")
    return render_template('generate_reports.html', years=years, months=months, 
                          current_year=current_year, current_month=current_month)

# 系統管理登入
@main_routes.route('/admin', methods=['GET', 'POST'])
@login_required
@authorized_required
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '5566':
            session['admin_logged_in'] = True
            logger.info("管理員登入成功")
            return redirect(url_for('main_routes.admin_dashboard'))
        else:
            logger.warning("管理員登入失敗，密碼錯誤")
            flash("密碼錯誤，請重新輸入")
    return render_template('admin_login.html')

# 系統管理儀表板
@main_routes.route('/admin/dashboard')
@login_required
@authorized_required
def admin_dashboard():
    if not session.get('admin_logged_in'):
        logger.warning("未授權的管理頁面訪問嘗試")
        flash("請先登入")
        return redirect(url_for('main_routes.admin_login'))
    
    logger.info("訪問管理控制台")
    return render_template('admin_dashboard.html')

# 系統設定頁面
@main_routes.route('/admin/system_config', methods=['GET', 'POST'])
@login_required
@authorized_required
def admin_system_config():
    if not session.get('admin_logged_in'):
        return redirect(url_for('main_routes.admin_login'))
    
    if request.method == 'POST':
        # 處理表單提交
        try:
            # 從表單獲取資料
            keys = request.form.getlist('key')
            values = request.form.getlist('value')
            
            # 創建DataFrame
            df = pd.DataFrame({
                '鍵': keys,
                '值': values
            })
            
            # 保存到資料庫
            success = save_master_data(df, '系統配置')
            
            if success:
                logger.info("系統配置更新成功")
                flash("系統配置已更新")
            else:
                logger.error("系統配置更新失敗")
                flash("系統配置更新失敗", "error")
                
        except Exception as e:
            logger.error(f"系統配置更新發生錯誤: {str(e)}")
            flash(f"發生錯誤: {str(e)}", "error")
    
    # 讀取當前系統配置
    system_config = read_master_data('系統配置')
    
    return render_template('admin_system_config.html', system_config=system_config.to_dict('records'))

# 員工與廠商管理頁面
@main_routes.route('/admin/staff_farmers', methods=['GET', 'POST'])
@login_required
@authorized_required
def admin_staff_farmers():
    if not session.get('admin_logged_in'):
        return redirect(url_for('main_routes.admin_login'))
    
    if request.method == 'POST':
        # 處理表單提交
        try:
            # 從表單獲取資料
            types = request.form.getlist('type')
            names = request.form.getlist('name')
            commission_rates = request.form.getlist('commission_rate')
            
            # 創建DataFrame
            df = pd.DataFrame({
                '類型': types,
                '名稱': names,
                '分潤比例': [float(rate) for rate in commission_rates]
            })
            
            # 保存到資料庫
            success = save_master_data(df, '員工廠商')
            
            if success:
                logger.info("員工與廠商資料更新成功")
                flash("員工與廠商資料已更新")
            else:
                logger.error("員工與廠商資料更新失敗")
                flash("員工與廠商資料更新失敗", "error")
                
        except Exception as e:
            logger.error(f"員工與廠商資料更新發生錯誤: {str(e)}")
            flash(f"發生錯誤: {str(e)}", "error")
    
    # 讀取當前員工與廠商資料
    staff_farmers = read_master_data('員工廠商')
    
    return render_template('admin_staff_farmers.html', staff_farmers=staff_farmers.to_dict('records'))

# 庫存管理頁面
@main_routes.route('/admin/inventory', methods=['GET', 'POST'])
@login_required
@authorized_required
def admin_inventory():
    if not session.get('admin_logged_in'):
        return redirect(url_for('main_routes.admin_login'))
    
    from models.data_manager import save_inventory
    
    if request.method == 'POST':
        # 處理表單提交
        try:
            # 從表單獲取資料
            product_ids = request.form.getlist('product_id')
            product_names = request.form.getlist('product_name')
            units = request.form.getlist('unit')
            quantities = request.form.getlist('quantity')
            unit_prices = request.form.getlist('unit_price')
            suppliers = request.form.getlist('supplier')
            
            # 創建DataFrame
            df = pd.DataFrame({
                '產品編號': [int(pid) for pid in product_ids],
                '產品名稱': product_names,
                '單位': units,
                '數量': [float(q) for q in quantities],
                '單價': [float(p) for p in unit_prices],
                '供應商': suppliers
            })
            
            # 保存到資料庫
            success = save_inventory(df)
            
            if success:
                logger.info("庫存資料更新成功")
                flash("庫存資料已更新")
            else:
                logger.error("庫存資料更新失敗")
                flash("庫存資料更新失敗", "error")
                
        except Exception as e:
            logger.error(f"庫存資料更新發生錯誤: {str(e)}")
            flash(f"發生錯誤: {str(e)}", "error")
    
    # 讀取當前庫存資料
    inventory_data = read_inventory()
    
    return render_template('admin_inventory.html', inventory=inventory_data.to_dict('records'))

# 交易紀錄管理頁面
@main_routes.route('/admin/transactions', methods=['GET', 'POST'])
@login_required
@authorized_required
def admin_transactions():
    if not session.get('admin_logged_in'):
        return redirect(url_for('main_routes.admin_login'))
    
    from models.data_manager import read_transactions
    
    if request.method == 'POST':
        # 處理表單提交 - 目前僅支援查詢，不支援編輯
        transaction_type = request.form.get('transaction_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        transactions_data = read_transactions(transaction_type, start_date, end_date)
        logger.info(f"查詢交易記錄: 類型={transaction_type}, 開始日期={start_date}, 結束日期={end_date}")
        
        return render_template('admin_transactions.html', 
                              transactions=transactions_data.to_dict('records'),
                              transaction_type=transaction_type,
                              start_date=start_date,
                              end_date=end_date)
    
    # 默認顯示所有交易記錄
    transactions_data = read_transactions()
    
    return render_template('admin_transactions.html', transactions=transactions_data.to_dict('records'))

# 管理員登出
@main_routes.route('/admin/logout')
@login_required
@authorized_required
def admin_logout():
    session.pop('admin_logged_in', None)
    logger.info("管理員登出")
    flash("已成功登出")
    return redirect(url_for('main_routes.index'))
