## 功能更新與調整 (YYYY-MM-DD)

### 銷貨退回 (Sales Return) 功能

- **目的**: 允許記錄顧客的銷售退貨，並正確調整庫存與影響財務報表。
- **主要變更**:
    - **庫存管理**: 
        - 移除了 `templates/admin_inventory.html` 頁面直接刪除庫存項目的按鈕和相關 JavaScript，現在庫存項目不能被輕易刪除，只能修改。
    - **資料模型 (`models/transactions.py`)**: 
        - 新增 `record_sales_return` 函數，用於記錄銷退交易。
        - 銷退交易會記錄負的總價，並增加相應產品的庫存數量。
    - **後端路由 (`routes/main_routes.py`)**: 
        - 新增 `/sales_return` 路由，處理銷退表單的顯示 (GET) 與提交 (POST)。
        - 路由包含權限驗證 (`@login_required`, `@authorized_required`)。
    - **前端模板 (`templates/sales_return.html`)**: 
        - 新建銷退登記表單頁面。
        - 表單包含日期、班別、員工、退貨產品、單位、數量、退貨單價和退貨原因等欄位。
        - JavaScript 會在選擇產品後，透過 `/api/product_details/<product_name>` API 動態獲取產品單位和預設退貨單價。
    - **功能選單 (`templates/select_operation.html`)**: 
        - 新增「銷貨退回」按鈕，連結至 `/sales_return` 頁面。
        - 為按鈕設定了新的 CSS 樣式 (青色系)。
    - **報表生成 (`models/report_generator.py`)**:
        - 修改 `generate_basic_reports` 和 `generate_farmer_detailed_reports` 函數以整合銷退數據。
        - **員工月報**: 
            - 新增「銷退總額」和「淨銷售額」欄位。
            - 員工分潤現在基於「淨銷售額」(毛銷售額 + 銷退總額) 計算。
        - **收支表月報**:
            - 調整項目以包含「總銷售額(毛額)」、「銷退總額」和「淨營業額」。
            - 「預估損益」的計算現在反映了銷退對營業額的影響。
        - **廠商詳細報表**:
            - 總覽頁加入「相關產品銷退總額」資訊。
            - 新增「相關產品銷退明細」工作表，列出與該廠商產品相關的顧客銷退記錄 (目前不直接影響廠商分潤計算)。

- **原因**: 
    - 滿足業務需求，允許處理顧客退貨的場景。
    - 確保庫存的準確性。
    - 使財務報表 (特別是分潤和損益) 能正確反映銷退的影響。
    - 防止意外刪除重要庫存資料，提高系統資料完整性。

### 銷貨退回 (Sales Return) 功能增強

- **目的**: 優化銷貨退回頁面的使用者體驗和資訊呈現，輔助使用者更準確地進行退貨操作。
- **主要變更**:
    - **後端 (`routes/main_routes.py`)**:
        - `sales_return` 路由 (GET): 修改為同時傳遞 `supplier_list` 到前端模板。
        - 新增 API `/api/supplier_products_for_return/<supplier_name>`: 用於根據廠商名稱獲取其供應過 (或庫存中) 的產品名稱列表，供銷退時選擇。
        - 新增 API `/api/product_unit_avg_purchase_price/<product_name>/<unit>`: 用於獲取特定產品和單位組合的平均進貨價。如果找不到進貨價，則嘗試返回當前售價作為備用。
        - 新增 API `/api/sales_transactions_for_return`: 接收 `supplier_name`, `product_name`, `unit` (均可選) 作為查詢參數，返回符合條件的歷史銷售記錄 (最新的在前，最多50筆)。
    - **資料模型 (`models/inventory.py`)**:
        - 新增 `get_product_avg_purchase_price(product_name, unit)` 函數: 從 `transactions` 表中查詢指定產品和單位的 `'進貨'` 記錄，計算並返回平均 `unit_price`。
    - **前端模板 (`templates/sales_return.html`)**:
        - **介面調整**: 
            - 頁面佈局調整為左右兩欄，左側為銷退表單，右側用於顯示相關銷售記錄。
            - 新增「選擇廠商」下拉選單。
        - **JavaScript 邏輯增強**:
            - **廠商產品聯動**: 選擇廠商後，通過 `/api/supplier_products_for_return/` 動態加載該廠商的產品到「退貨產品名稱」下拉選單。
            - **單位選擇修復與聯動**: 選擇產品後，通過 `/api/product_details/` 動態加載該產品的單位到「單位」下拉選單 (此為對之前選擇單位的改進和確認)。
            - **預設退貨單價**: 選擇單位後，通過 `/api/product_unit_avg_purchase_price/` 動態獲取平均進貨價 (或備用售價)，並自動填入「退貨單價」欄位，該欄位保持可編輯。
            - **銷售記錄顯示**: 在選擇廠商、產品、單位後，通過 `/api/sales_transactions_for_return` 動態查詢並在頁面右側表格中顯示相關的歷史銷售記錄，幫助使用者參考。
            - 事件監聽器調整以確保在適當時機觸發數據獲取和刷新。

- **原因**: 
    - 提升使用者操作效率：通過廠商篩選產品，簡化產品選擇過程。
    - 提供決策輔助：自動帶入平均進貨價作為退貨單價參考，但允許修改以應對特殊情況。
    - 增加操作透明度：顯示相關銷售歷史，方便使用者確認退貨的依據，減少錯誤。
    - 修復先前版本中選擇產品後可能無法正確選擇單位的問題。

## 修復與調整 (YYYY-MM-DD)

### 銷貨退回功能導入錯誤修復

- **問題描述**: 在 `models/transactions.py` 的 `record_sales_return` 函數中，嘗試導入一個不存在的 `update_inventory` 函數 (從 `models/inventory.py`)，導致 `ImportError`。

- **主要變更 (`models/transactions.py`)**:
    - **移除錯誤導入**: 刪除了 `from models.inventory import ..., update_inventory` 中的 `update_inventory`。
    - **庫存更新邏輯調整**: 
        - 在 `record_sales_return` 函數內部，當需要更新庫存時：
            1. 使用 `get_product_details(product_name)` 獲取產品的詳細資訊 (包含 `product_id` 和不同單位的資訊)。
            2. 從產品詳細資訊中，根據傳入的 `unit` 找到對應的 `product_id`。
            3. 使用獲取的 `product_id`、`unit` 和銷退的 `quantity` (正數，代表增加庫存) 來呼叫現有的 `update_inventory_quantity(product_id, unit, quantity_change)` 函數。
    - **交易數據鍵名統一**: 
        - 傳遞給 `db_manager.add_transaction()` 的銷退交易數據字典 (`db_transaction_data`) 的鍵名，已調整為與其他交易類型 (如進貨、銷售) 的鍵名一致，例如使用 `'交易類型'`, `'產品編號'`, `'供應商'`, `'退貨原因'` 等。
        - 銷退記錄中現在會包含產品的原始 `'供應商'` (從 `get_product_details` 獲取)。
    - **時間格式統一**:
        - 銷退交易記錄中的 `'時間'` 欄位現在使用 `HH:MM:SS` 格式，與其他交易記錄保持一致。

- **原因**: 
    - 原先的 `update_inventory` 函數並不存在於 `models/inventory.py` 中，導致程式啟動時發生導入錯誤。
    - 需要使用正確的庫存更新方法 (`update_inventory_quantity`) 並提供其所需的參數 (`product_id`)。
    - 確保資料庫中不同類型交易記錄的欄位名稱和格式具有一致性，方便後續的數據處理和報表生成。 

### 銷貨退回頁面排版與 Linter 錯誤調整

- **目的**: 修正銷貨退回頁面 (`templates/sales_return.html`) 左側表單和右側銷售記錄區塊被擠壓到左邊的排版問題，並處理相關的 Linter 錯誤。
- **主要變更 (`templates/sales_return.html`)**:
    - **CSS 樣式調整 (內聯 `<style>`)**:
        - 為 `body > .container` 設定 `max-width: 95%;` 和 `margin: 20px auto;`，確保主內容區有足夠寬度並居中。
        - 為 `.form-container` (包含左右兩欄的容器) 設定 `width: 100%;` 和 `flex-wrap: nowrap;`。
        - 調整 `.form-left` (表單區) 的 `flex` 屬性為 `2 1 500px`，並設定 `min-width: 450px`，增加右邊距和右邊框作為分隔。
        - 調整 `.form-right` (銷售記錄區) 的 `flex` 屬性為 `3 1 60%`，設定 `min-width: 300px`，並將 `max-height` 改為 `70vh`。
        - 針對 `.form-left` 內的 `.form-row` 和 `.form-group` 添加 flex 佈局樣式，改善表單內部元素的排列和響應性。
        - 確保表單輸入框 (`input`, `select`, `textarea`) 使用 `width: 100%;` 和 `box-sizing: border-box;` 以正確填充其容器。
    - **Linter 錯誤處理**:
        - 嘗試修改返回按鈕 `onclick` 事件中 `url_for` 的引號用法，以解決 Linter 提出的 `Unterminated string literal` 和 `';' expected` 錯誤。多次嘗試後，Linter 錯誤依然存在且提示不一致，暫時保留在瀏覽器中能正常工作的版本，Linter 報錯可能為誤報或需特殊配置。
- **原因**:
    - 原有 CSS 未能有效控制左右兩欄的寬度和佈局，導致在高解析度或特定內容下出現擠壓。
    - 新增的 CSS 規則旨在提供更穩健的 Flexbox 佈局，確保左右兩欄能按預期比例分配空間，並在不同螢幕尺寸下有合理的最小寬度。
    - Linter 錯誤可能源於其解析 HTML 內嵌 JavaScript（尤其是混合 Jinja 模板）的限制。 

### 銷貨退回邏輯調整：產品選擇基於進貨歷史

- **目的**: 修正銷貨退回功能中，可選擇退貨的產品列表僅來自當前庫存的問題，確保即使產品已售罄或不再庫存中，只要歷史上有進貨記錄，仍可進行銷退。
- **主要變更**:
    - **資料模型 (`models/inventory.py`)**:
        - 新增函數 `get_product_names_from_purchase_history(supplier_name)`：此函數查詢 `transactions` 表，找出特定供應商所有 `'進貨'`類型交易中不重複的產品名稱列表。
        - 修改原 `get_products_by_supplier(supplier)` 函數的註釋，明確其功能是從當前 `inventory` 表中查詢產品。
    - **後端路由 (`routes/main_routes.py`)**:
        - 修改 `/api/supplier_products_for_return/<supplier_name>` API 端點的實現：
            - 導入新的 `get_product_names_from_purchase_history` 函數。
            - 改為調用此新函數來獲取產品名稱列表，替代之前從當前庫存獲取產品的邏輯。
            - 相應更新了日誌記錄信息。
- **原因**:
    - 銷貨退回的本質是針對已售出的商品進行退貨，因此可退貨的產品範圍應基於歷史銷售/進貨記錄，而非當前是否有庫存。
    - 此修改確保了業務邏輯的正確性，允許用戶為任何曾經銷售過的產品（只要能追溯到其供應商和進貨記錄）辦理退貨。

### 銷貨退回頁面：修復銷售記錄查詢的 KeyError

- **目的**: 解決在銷貨退回頁面查詢相關銷售記錄時，因欄位名稱不匹配導致的 `KeyError: 'supplier'` 問題。
- **主要變更 (`routes/main_routes.py`)**:
    - 在 `api_sales_transactions_for_return` 函數中：
        - 分析 `models/data_manager.py` 中的 `read_transactions` 函數發現，從資料庫查詢交易時，`supplier` 欄位被重命名為 `'供應商'` (`supplier AS 供應商`)。
        - 因此，將篩選 DataFrame 時對供應商欄位的引用從 `sales_df['supplier']` 修改為 `sales_df['供應商']`。
        - 同時確認了其他用於篩選（如 `'產品名稱'`, `'單位'`）和最終顯示（`columns_to_show`）的欄位名與 `read_transactions` 返回的 DataFrame 中的中文欄位名一致。
- **原因**:
    - API 端點在嘗試篩選銷售記錄 DataFrame 時使用了英文欄位名 `'supplier'`，而 `read_transactions` 函數返回的 DataFrame 中該欄位名為中文 `'供應商'`，導致 `KeyError`。
    - 此修改統一了代碼中對該欄位名的引用，確保篩選邏輯能正確執行。 

### 銷貨退回流程重構：從表單填寫改為選擇歷史銷售記錄整單退貨

- **目的**: 徹底改變銷貨退回的操作方式，從手動填寫退貨詳情改為從歷史銷售記錄中選擇一筆進行整單退貨，以簡化操作並確保數據一致性。
- **主要變更**:
    - **資料模型 (`models/transactions.py`)**:
        - `record_sales_return` 函數重構：
            - 函數簽名變更為 `record_sales_return(original_transaction_id: str, staff: str, reason: str = "")`。
            - 內部邏輯修改為：
                1. 根據 `original_transaction_id` 從 `transactions` 表查詢原始銷售記錄。
                2. 使用原始銷售記錄的數據（產品、數量、單價、供應商等）創建一筆新的 `'銷退'` 交易記錄。
                3. 銷退記錄的總價為原始銷售總價的負值。
                4. 銷退日期為當前操作日期。
                5. 原始銷售的交易ID會被記錄在銷退單的 `'退貨原因'` 欄位中 (例如：`"原因 (原始單號: XXXXX)"`)，因目前 `transactions` 表無專用欄位。
                6. 調用 `add_transaction` 存儲新的銷退記錄。
                7. 調用 `update_inventory_quantity` 將原始銷售的產品數量加回庫存。
    - **後端路由 (`routes/main_routes.py`)**:
        - `/sales_return` 路由 (POST 方法) 修改：
            - 不再接收詳細的產品、數量、價格等表單數據。
            - 改為接收 `original_transaction_id` (從前端選擇的銷售記錄ID)、`staff` (處理退貨的員工) 和 `reason` (退貨原因)。
            - 調用重構後的 `record_sales_return` 函數處理退貨邏輯。
            - 更新相應的 `flash` 消息和日誌記錄。
        - `/sales_return` 路由 (GET 方法):
            - 傳遞給模板的數據（如員工列表、廠商列表）保持不變，用於支持新的篩選界面。
    - **前端模板 (`templates/sales_return.html`)**:
        - **介面大幅修改**:
            - 移除了原先的詳細銷退項目填寫表單。
            - 頁面上方設置為「篩選銷售記錄」區域，包含：
                - 廠商選擇 (下拉)。
                - 產品名稱篩選 (文字輸入)。
                - 單位篩選 (文字輸入)。
                - 「查詢銷售記錄」按鈕。
            - 篩選區域下方是一個獨立的 `<form>`，用於實際提交退貨請求。此表單包含：
                - 一個隱藏的 `input` 欄位 (`original_transaction_id`)。
                - 一個可見的「處理員工」下拉選單 (必填)。
                - 一個可見的「退貨原因」文本域 (選填)。
            - 頁面主要區域用於通過 JavaScript 動態加載和顯示「符合條件的銷售記錄」表格。
        - **JavaScript 邏輯重構**:
            - 「查詢銷售記錄」按鈕點擊後，調用 `/api/sales_transactions_for_return` API，並將返回的銷售記錄渲染成表格。
            - 每條銷售記錄在表格中會有一列「操作」，內含一個「整單退貨」按鈕。
            - 點擊「整單退貨」按鈕：
                1. 彈出確認對話框。
                2. 用戶確認後，將該條銷售記錄的 `交易ID` 賦值給隱藏表單中的 `original_transaction_id` 欄位。
                3. 從「處理員工」下拉選單獲取員工姓名，從「退貨原因」文本域獲取原因。
                4. 提交包含 `original_transaction_id`、`staff` 和 `reason` 的表單到 `/sales_return` (POST)。
        - **樣式調整**: 配合新的佈局和元素調整了 CSS。
        - **Linter 提示**: 返回按鈕的 `onclick` 中的 `url_for` 寫法，Linter 仍提示 `';' expected`，此為已知Linter解析問題，暫不修改，因不影響實際功能。

- **原因**:
    - **簡化用戶操作**: 用戶不再需要手動填寫大量退貨細節，只需選擇一筆已存在的銷售記錄。
    - **提高數據準確性**: 退貨信息直接來源於原始銷售單，減少了手動輸入錯誤的可能。
    - **確保賬務和庫存一致性**: 整單退貨的邏輯確保了銷退記錄的金額和數量與原始銷售單完全對應（金額相反），庫存也能正確回補。
    - 使退貨流程更貼近實際業務場景中的「取消交易」或「原單退貨」。 