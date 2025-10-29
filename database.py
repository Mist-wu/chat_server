import sqlite3
import json
from datetime import datetime

DATABASE_FILE = 'chat_history.db'

def init_db():
    """初始化数据库并创建表（如果不存在）。"""
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    cursor = conn.cursor()
    # 原有的对话历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            user_id TEXT PRIMARY KEY,
            history TEXT NOT NULL
        )
    ''')
    # 新增：用户身份设置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id TEXT PRIMARY KEY,
            identity_id INTEGER DEFAULT 0
        )
    ''')
    # 新增：访问日志表
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
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT history FROM conversations WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        # 从数据库中读取JSON字符串并解析为Python对象
        return json.loads(row[0])
    return None

def update_user_session(user_id, history):
    """更新或创建用户的对话历史。"""
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    cursor = conn.cursor()
    # 将Python对象序列化为JSON字符串以便存入数据库
    history_json = json.dumps(history, ensure_ascii=False)
    # 使用 INSERT OR REPLACE 来处理新用户创建和老用户更新
    cursor.execute('INSERT OR REPLACE INTO conversations (user_id, history) VALUES (?, ?)', (user_id, history_json))
    conn.commit()
    conn.close()

def clear_user_history(user_id):
    """清空指定用户的对话历史。"""
    # 通过更新为空的JSON数组来清空历史
    update_user_session(user_id, [])

def set_user_identity(user_id, identity_id):
    """设置或更新用户的AI身份。"""
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO user_settings (user_id, identity_id) VALUES (?, ?)', (user_id, identity_id))
    conn.commit()
    conn.close()

def get_user_identity(user_id):
    """获取用户的AI身份，如果不存在则创建默认值。"""
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT identity_id FROM user_settings WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return row[0]
    else:
        # 用户首次查询时，为其创建默认身份设置
        cursor.execute('INSERT INTO user_settings (user_id, identity_id) VALUES (?, 0)', (user_id,))
        conn.commit()
        conn.close()
        return 0

def log_access(user_id):
    """记录用户访问。"""
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO access_log (user_id, timestamp) VALUES (?, CURRENT_TIMESTAMP)', (user_id,))
    conn.commit()
    conn.close()

def get_access_stats():
    """获取访问统计数据（总用户数和今日用户数）。"""
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    cursor = conn.cursor()
    
    # 累计独立访问用户数
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM access_log")
    total_users = cursor.fetchone()[0]
    
    # 今日独立访问用户数
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM access_log WHERE DATE(timestamp) = ?", (today_str,))
    today_users = cursor.fetchone()[0]
    
    conn.close()
    return total_users, today_users
