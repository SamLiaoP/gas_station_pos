"""
SQLite Manager for cloud integrations
Entry point for SQLite database operations
"""
from utils.cloud.sqlite.cloud_manager import CloudSQLiteManager

# 直接從子模組導出 CloudSQLiteManager 類
__all__ = ['CloudSQLiteManager']
