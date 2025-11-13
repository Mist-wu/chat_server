import sqlite3
import json
from datetime import datetime
from flask import g # 导入g

DATABASE_FILE = 'chat_history.db'

def get_db():
    """
    获取当前请求的数据库连接。
    如果连接不存在，则创建一个新的连接并存储在g对象中。
    """
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE_FILE) # 移除 check_same_thread=False
        g.db.row_factory = sqlite3.Row # 让连接返回类似字典的行
    return g.db

# init_db 可以在应用启动时独立调用，保持不变
def init_db():
    """初始化数据库并创建表（如果不存在）。"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    # 原有的对话历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            user_id TEXT PRIMARY KEY,
            history TEXT NOT NULL
        )
    ''')
    # 用户设置表，增加 pending_action 字段
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id TEXT PRIMARY KEY,
            identity_id INTEGER DEFAULT 0,
            pending_action TEXT 
        )
    ''')
    # 访问日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_user_session(user_id):
    """根据用户ID检索对话历史。"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT history FROM conversations WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row:
        return json.loads(row[0])
    return None

def update_user_session(user_id, history):
    """更新或创建用户的对话历史。"""
    db = get_db()
    history_json = json.dumps(history, ensure_ascii=False)
    db.execute('INSERT OR REPLACE INTO conversations (user_id, history) VALUES (?, ?)', (user_id, history_json))
    db.commit()

def clear_user_history(user_id):
    """清空指定用户的对话历史。"""
    update_user_session(user_id, [])

def set_user_identity(user_id, identity_id):
    """设置或更新用户的AI身份。"""
    db = get_db()
    db.execute('INSERT OR REPLACE INTO user_settings (user_id, identity_id) VALUES (?, ?)', (user_id, identity_id))
    db.commit()

def get_user_identity(user_id):
    """获取用户的AI身份，如果不存在则创建默认值。"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT identity_id FROM user_settings WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        # 使用 INSERT OR IGNORE 避免在多线程环境下重复插入
        db.execute('INSERT OR IGNORE INTO user_settings (user_id, identity_id) VALUES (?, 0)', (user_id,))
        db.commit()
        return 0

def get_user_setting(user_id, key):
    """获取用户的特定设置项。"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row and key in row.keys():
        return row[key]
    return None

def update_user_setting(user_id, key, value):
    """更新用户的特定设置项。"""
    db = get_db()
    # 确保用户记录存在
    get_user_identity(user_id)
    # 更新特定字段
    db.execute(f'UPDATE user_settings SET {key} = ? WHERE user_id = ?', (value, user_id))
    db.commit()

def log_access(user_id):
    """记录用户访问。"""
    db = get_db()
    db.execute('INSERT INTO access_log (user_id, timestamp) VALUES (?, CURRENT_TIMESTAMP)', (user_id,))
    db.commit()

def get_access_stats():
    """获取访问统计数据（总用户数和今日用户数）。"""
    db = get_db()
    cursor = db.cursor()
    
    # 累计独立访问用户数
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM access_log")
    total_users = cursor.fetchone()[0]
    
    # 今日独立访问用户数
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM access_log WHERE DATE(timestamp) = ?", (today_str,))
    today_users = cursor.fetchone()[0]
    
    return total_users, today_users