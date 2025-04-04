# 更新Excel欄位到繁體中文

要將所有Excel文件的欄位更新為繁體中文，請執行以下命令：

```bash
# 確保腳本可執行
chmod +x update_excel_files.sh

# 執行腳本
./update_excel_files.sh
```

或者直接執行Python腳本：

```bash
python create_excel_files_chinese.py
```

這將重新生成所有Excel檔案，並確保所有欄位名稱使用繁體中文。

**注意**：這將重置所有Excel檔案，如果您有任何已經輸入的資料可能會被覆蓋。如果需要保留現有資料，請先備份data目錄中的文件。
