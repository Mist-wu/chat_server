"""
命令行测试工具 - 模拟微信客户端功能
通过向 main.py 的 HTTP 接口发送请求来测试
"""

import requests
import time
import hashlib
import xml.etree.ElementTree as ET

# 配置
SERVER_URL = "http://127.0.0.1:80"  # main.py 运行的地址
TOKEN = "mist"  # 与 config.py 中的 TOKEN 一致
TEST_USER_ID = "test_user_from_terminal"  # 模拟的用户 OpenID
BOT_ID = "gh_test_bot"  # 模拟的公众号ID


def generate_signature(timestamp: str, nonce: str) -> str:
    """
    生成微信验证签名
    """
    tmp_list = [TOKEN, timestamp, nonce]
    tmp_list.sort()
    tmp_str = ''.join(tmp_list)
    return hashlib.sha1(tmp_str.encode('utf-8')).hexdigest()


def build_message_xml(content: str) -> str:
    """
    构建发送给服务器的微信消息 XML
    """
    timestamp = int(time.time())
    msg_id = str(int(time.time() * 1000))  # 模拟消息ID
    
    xml_template = f"""<xml>
    <ToUserName><![CDATA[{BOT_ID}]]></ToUserName>
    <FromUserName><![CDATA[{TEST_USER_ID}]]></FromUserName>
    <CreateTime>{timestamp}</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[{content}]]></Content>
    <MsgId>{msg_id}</MsgId>
</xml>"""
    return xml_template


def parse_response_xml(xml_str: str) -> str:
    """
    解析服务器返回的 XML，提取回复内容
    """
    if not xml_str or xml_str.strip() == "success":
        return "[服务器返回: success]"
    
    try:
        root = ET.fromstring(xml_str)
        content = root.find('Content')
        if content is not None and content.text:
            return content.text
        else:
            return f"[无法解析的响应: {xml_str[:100]}...]"
    except ET.ParseError:
        return f"[XML解析失败: {xml_str[:100]}...]"


def send_message(content: str) -> str:
    """
    向服务器发送消息并获取回复
    """
    # 构建请求数据
    xml_data = build_message_xml(content)
    
    # 生成签名参数
    timestamp = str(int(time.time()))
    nonce = "test_nonce_123"
    signature = generate_signature(timestamp, nonce)
    
    # 发送 POST 请求
    try:
        response = requests.post(
            SERVER_URL,
            data=xml_data.encode('utf-8'),
            params={
                'signature': signature,
                'timestamp': timestamp,
                'nonce': nonce
            },
            headers={'Content-Type': 'application/xml'},
            timeout=30
        )
        response.encoding = 'utf-8'
        return parse_response_xml(response.text)
    except requests.exceptions.ConnectionError:
        return "[错误] 无法连接到服务器，请确保 main.py 已启动 (python main.py)"
    except requests.exceptions.Timeout:
        return "[错误] 请求超时"
    except Exception as e:
        return f"[错误] {e}"


def verify_server() -> bool:
    """
    验证服务器是否正常运行（模拟微信服务器验证）
    """
    timestamp = str(int(time.time()))
    nonce = "verify_nonce"
    echostr = "verify_success"
    signature = generate_signature(timestamp, nonce)
    
    try:
        response = requests.get(
            SERVER_URL,
            params={
                'signature': signature,
                'timestamp': timestamp,
                'nonce': nonce,
                'echostr': echostr
            },
            timeout=5
        )
        return response.text == echostr
    except:
        return False


def main():
    """
    主函数 - 命令行交互循环
    """
    print("=" * 50)
    print("微信客户端模拟器 - 命令行测试工具")
    print(f"服务器地址: {SERVER_URL}")
    print(f"模拟用户ID: {TEST_USER_ID}")
    print("=" * 50)
    
    # 检查服务器连接
    print("正在检查服务器连接...")
    if verify_server():
        print("✓ 服务器连接正常")
    else:
        print("✗ 无法连接服务器，请先启动 main.py")
        print("  运行命令: python main.py")
        print("=" * 50)
        print("提示: 你也可以继续尝试发送消息")
    
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
            
            # 发送消息并获取回复
            reply = send_message(user_input)
            
            # 显示回复
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