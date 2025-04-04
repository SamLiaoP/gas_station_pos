from flask import render_template, request, redirect, url_for, jsonify, Blueprint
from utils.common import get_taiwan_time, logger
from utils.config import get_current_shift
from models.data_manager import get_staff_and_farmers, get_inventory
from models.inventory import get_product_details
from models.transactions import record_purchase, record_sale
from models.report_generator import generate_reports

main_routes = Blueprint('main_routes', __name__)

# 主頁路由
@main_routes.route('/')
def index():
    today = get_taiwan_time().strftime('%Y-%m-%d')
    current_shift = get_current_shift()
    logger.info(f"訪問首頁，日期：{today}，班別：{current_shift}")
    return render_template('index.html', today=today, current_shift=current_shift)

# 選擇操作頁面
@main_routes.route('/select_operation')
def select_operation():
    logger.info("訪問選擇操作頁面")
    return render_template('select_operation.html')

# 進貨頁面
@main_routes.route('/purchase', methods=['GET', 'POST'])
def purchase():
    if request.method == 'POST':
        # 從表單提交中提取日期
        date = request.form.get('date')
        farmer = request.form.get('farmer')
        product_name = request.form.get('product_name')
        unit = request.form.get('unit')
        quantity = float(request.form.get('quantity'))
        unit_price = float(request.form.get('unit_price'))
        staff = request.form.get('staff')
        
        logger.info(f"進貨記錄：日期={date}, 小農={farmer}, 產品={product_name}, 單位={unit}, 數量={quantity}, 單價={unit_price}, 員工={staff}")
        
        try:
            success = record_purchase(date, farmer, product_name, unit, quantity, unit_price, staff)
            
            if success:
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
    
    staff, farmers = get_staff_and_farmers()
    logger.info(f"訪問進貨頁面，加載員工列表{staff}和小農列表{farmers}")
    return render_template('purchase.html', staff=staff, farmers=farmers)

# 銷售頁面
@main_routes.route('/sale', methods=['GET', 'POST'])
def sale():
    if request.method == 'POST':
        # 從表單提交中提取日期和班別
        date = request.form.get('date')
        shift = request.form.get('shift')
        staff = request.form.get('staff')
        product_name = request.form.get('product_name')
        unit = request.form.get('unit')
        quantity = float(request.form.get('quantity'))
        unit_price = float(request.form.get('unit_price'))
        
        logger.info(f"銷售記錄：日期={date}, 班別={shift}, 員工={staff}, 產品={product_name}, 單位={unit}, 數量={quantity}, 單價={unit_price}")
        
        try:
            # 檢查庫存是否足夠
            inventory = get_inventory()
            matching_rows = inventory[(inventory['產品名稱'] == product_name) & (inventory['單位'] == unit)]
            
            if not matching_rows.empty:
                current_quantity = matching_rows.iloc[0]['數量']
                if current_quantity < quantity:
                    logger.error(f"庫存不足！當前庫存: {current_quantity} {unit}, 所需數量: {quantity} {unit}")
                    return f"庫存不足！當前庫存: {current_quantity} {unit}, 所需數量: {quantity} {unit}", 400
            else:
                logger.error(f"找不到產品 {product_name} 的 {unit} 單位庫存")
                return f"找不到產品 {product_name} 的 {unit} 單位庫存", 400
            
            success = record_sale(date, shift, staff, product_name, unit, quantity, unit_price)
            
            if success:
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
    inventory = get_inventory()
    # 取得有庫存的產品列表（確保產品名稱不重複）
    products = inventory[inventory['數量'] > 0]['產品名稱'].unique().tolist()
    
    logger.info(f"訪問銷售頁面，加載員工列表{staff}和產品列表{products}")
    return render_template('sale.html', staff=staff, products=products)

# 獲取產品詳情API
@main_routes.route('/api/product_details/<product_name>')
def api_product_details(product_name):
    try:
        # 打印診斷信息
        logger.info(f"API請求產品詳情：'{product_name}'")
        
        details = get_product_details(product_name)
        if details:
            # 確保回傳結果包含所有必要的資訊
            if 'units' not in details or not details['units']:
                logger.error(f"產品 '{product_name}' 的 units 列表為空或不存在")
                return jsonify({"error": "產品單位資料不完整"}), 500
                
            logger.info(f"回傳 API 結果: 找到 {len(details['units'])} 種單位，詳情：{details['units']}")
            
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

# 庫存API
@main_routes.route('/api/inventory')
def api_inventory():
    logger.info("訪問庫存API")
    inventory_data = get_inventory()
    return jsonify(inventory_data.to_dict('records'))

# 庫存頁面
@main_routes.route('/inventory')
def inventory():
    logger.info("訪問庫存頁面")
    inventory_data = get_inventory()
    logger.info(f"庫存數據計數：{len(inventory_data)}")
    return render_template('inventory.html', inventory=inventory_data.to_dict('records'))

# 報表下載功能
@main_routes.route('/download_report/<path:path>')
def download_report(path):
    from flask import send_file
    from utils.common import REPORTS_PATH
    import os
    
    report_path = os.path.join(REPORTS_PATH, path)
    
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True)
    else:
        return f"找不到報表文件: {path}", 404

# 生成報表頁面
@main_routes.route('/generate_reports', methods=['GET', 'POST'])
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
        
        logger.info(f"開始生成報表：{date_range_str}，包含小農詳細報表: {generate_farmer_details}")
        
        # 生成報表
        success, report_dir, report_files = generate_reports(
            year=year, 
            month=month, 
            start_date=start_date, 
            end_date=end_date, 
            generate_farmer_details=generate_farmer_details,
            url_for_func=url_for
        )
        
        if success:
            logger.info(f"報表生成成功，儲存於：{report_dir}")
            
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
