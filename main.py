import hashlib
import time
from flask import Flask, request
import xml.etree.ElementTree as ET
import config
import chatAI
import database
import command_handler # 导入新的指令处理模块
import weather
import threading

# --- Flask Web 应用 ---
app = Flask(__name__)

def schedule_weather_updates():
    """
    定时任务函数，每小时更新一次天气缓存。
    """
    while True:
        weather.update_weather_cache()
        # 等待1小时
        time.sleep(3600)

@app.route('/', methods=['GET', 'POST'])
def wechat():
    if request.method == 'GET':
        # --- 微信服务器验证 ---
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')

        tmp_list = [config.TOKEN, str(timestamp), str(nonce)]
        tmp_list.sort()
        tmp_str = ''.join(tmp_list)
        hashcode = hashlib.sha1(tmp_str.encode('utf-8')).hexdigest()
        
        if hashcode == signature:
            return echostr
        else:
            return 'token验证失败'
    else:
        # --- 接收并处理微信消息 ---
        xml_data = request.data
        if not xml_data:
            return "success"
            
        try:
            xml_rec = ET.fromstring(xml_data)
            
            # 提取消息内容
            to_user_name = xml_rec.find('ToUserName').text
            from_user_name = xml_rec.find('FromUserName').text
            msg_type = xml_rec.find('MsgType').text

            # 记录用户访问
            database.log_access(from_user_name)

            if msg_type == 'text':
                user_input = xml_rec.find('Content').text.strip()
                
                # --- 指令处理系统 ---
                if user_input.startswith("/"):
                    reply_content = command_handler.handle_command(user_input, from_user_name)
                    
                    # 构造回复XML
                    reply_xml = f"""
                    <xml>
                        <ToUserName><![CDATA[{from_user_name}]]></ToUserName>
                        <FromUserName><![CDATA[{to_user_name}]]></FromUserName>
                        <CreateTime>{int(time.time())}</CreateTime>
                        <MsgType><![CDATA[text]]></MsgType>
                        <Content><![CDATA[{reply_content}]]></Content>
                    </xml>
                    """
                    return reply_xml
                else:
                    # --- 正常对话处理 ---
                    ai_reply_content = chatAI.get_response(from_user_name, user_input)
                    ai_reply_content = ai_reply_content.strip()
                    
                    # 构造回复的XML
                    reply_xml = f"""
                    <xml>
                        <ToUserName><![CDATA[{from_user_name}]]></ToUserName>
                        <FromUserName><![CDATA[{to_user_name}]]></FromUserName>
                        <CreateTime>{int(time.time())}</CreateTime>
                        <MsgType><![CDATA[text]]></MsgType>
                        <Content><![CDATA[{ai_reply_content}]]></Content>
                    </xml>
                    """
                    return reply_xml
            else:
                # 对于非文本消息，可以简单回复或不处理
                return "success"

        except Exception:
            # 在服务器环境中，我们不打印错误，只返回success，避免微信重试
            return "success"

if __name__ == '__main__':
    # 初始化数据库
    database.init_db()

    # 首次立即更新天气缓存
    weather.update_weather_cache()

    # 启动后台线程定时更新天气
    update_thread = threading.Thread(target=schedule_weather_updates, daemon=True)
    update_thread.start()

    # 运行 Flask 应用来对接微信
    app.run(host='0.0.0.0', port=80)