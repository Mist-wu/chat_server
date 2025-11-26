"""
命令行测试工具 - 模拟微信聊天功能
用于在本地测试 chatAI 和 command_handler 的功能
"""

import config
import chatAI
import database
import command_handler
from flask import Flask

# 创建一个临时的 Flask 应用用于提供应用上下文
app = Flask(__name__)

# 模拟的用户ID，使用管理员ID
TEST_USER_ID = config.ADMIN_USER_ID[0] if config.ADMIN_USER_ID else 'test_admin_user'


def process_message(user_input: str) -> str:
    """
    处理用户输入，模拟 main.py 中的消息处理逻辑。
    """
    user_input = user_input.strip()
    
    if not user_input:
        return ""
    
    # 指令处理
    if user_input. startswith("/"):
        return command_handler.handle_command(user_input, TEST_USER_ID)
    else:
        # 正常对话处理
        return chatAI.get_response(TEST_USER_ID, user_input)


def main():
    """
    主函数 - 命令行交互循环
    """
    # 初始化数据库
    database.init_db()
    
    print("=" * 50)
    print("命令行聊天测试工具")
    print(f"当前用户ID: {TEST_USER_ID}")
    print(f"用户身份: 管理员" if TEST_USER_ID in config.ADMIN_USER_ID else "用户身份: 普通用户")
    print("=" * 50)
    print("输入消息开始聊天，输入 'exit' 或 'quit' 退出")
    print("输入 '/指令' 查看所有可用指令")
    print("=" * 50)
    print()
    
    while True:
        try:
            # 获取用户输入
            user_input = input("你: ").strip()
            
            # 退出命令
            if user_input.lower() in ('exit', 'quit', '退出'):
                print("再见！")
                break
            
            # 跳过空输入
            if not user_input:
                continue
            
            # 在应用上下文中处理消息
            with app.app_context():
                reply = process_message(user_input)
            
            # 显示回复
            if reply:
                print(f"AI: {reply}")
            print()
            
        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            print()


if __name__ == '__main__':
    main()