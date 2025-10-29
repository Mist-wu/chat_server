import hashlib
import time
from flask import Flask, request
import xml.etree.ElementTree as ET
import config
import chatAI
import database
import random
from datetime import datetime

# --- Flask Web 应用 ---
app = Flask(__name__)

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
                    command_parts = user_input.split(maxsplit=1)
                    command = command_parts[0]
                    args = command_parts[1] if len(command_parts) > 1 else ""
                    reply_content = "未知指令或格式错误。" # 默认回复
                    is_admin = from_user_name in config.ADMIN_USER_ID

                    # --- 通用指令 ---
                    if command == '/意见':
                        if args:
                            with open(config.FEEDBACK_FILE, 'a', encoding='utf-8') as f:
                                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{from_user_name}] {args}\n")
                            reply_content = "感谢你的反馈！"
                        else:
                            reply_content = "指令格式错误，请使用：/意见 [内容]"

                    elif command == '/身份列表':
                        reply_content = "可选身份列表：\n"
                        for id, persona in config.PERSONAS.items():
                            reply_content += f"{id}. {persona['name']}\n"
                        reply_content += "使用 /身份 [数字] 切换，/身份 0 恢复默认。"

                    elif command == '/身份':
                        try:
                            identity_id = int(args)
                            if identity_id == 0 or str(identity_id) in config.PERSONAS:
                                database.set_user_identity(from_user_name, identity_id)
                                if identity_id == 0:
                                    reply_content = "已恢复默认身份。"
                                else:
                                    reply_content = f"身份已切换为：{config.PERSONAS[str(identity_id)]['name']}"
                            else:
                                reply_content = "无效的身份编号。"
                        except (ValueError, KeyError):
                            reply_content = "指令格式错误或身份编号无效，请使用：/身份 [数字]"

                    elif command == '/当前身份':
                        identity_id = database.get_user_identity(from_user_name)
                        if identity_id == 0:
                            reply_content = "当前为默认身份。"
                        else:
                            persona = config.PERSONAS.get(str(identity_id))
                            reply_content = f"当前身份：{persona['name'] if persona else '未知身份'}"
                    
                    elif command == '/清空历史':
                        database.clear_user_history(from_user_name)
                        reply_content = "您的对话历史已清空。"

                    elif command == '/随机身份':
                        random_id_str = random.choice(list(config.PERSONAS.keys()))
                        database.set_user_identity(from_user_name, int(random_id_str))
                        reply_content = f"已随机切换身份为：{config.PERSONAS[random_id_str]['name']}"
                    
                    elif command == '/指令':
                        doc_file = 'command_system.md' if is_admin else 'command_user.md'
                        try:
                            with open(doc_file, 'r', encoding='utf-8') as f:
                                reply_content = f.read()
                        except FileNotFoundError:
                            reply_content = "指令文档丢失，请联系管理员。"

                    # --- 管理员专用指令 ---
                    elif is_admin:
                        if command == '/反馈列表':
                            try:
                                with open(config.FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                                    lines = f.readlines()
                                if not lines:
                                    reply_content = "目前没有反馈。"
                                else:
                                    reply_content = "最近30条反馈：\n" + "".join(lines[-30:])
                            except FileNotFoundError:
                                reply_content = "目前没有反馈。"
                        
                        elif command == '/访问':
                            total, today = database.get_access_stats()
                            reply_content = f"累计访问人数：{total}\n今日访问人数：{today}"

                        elif command == '/清除反馈':
                            try:
                                with open(config.FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                                    lines = f.readlines()
                                if len(lines) <= 30:
                                    open(config.FEEDBACK_FILE, 'w').close()
                                    reply_content = "已清除所有反馈。"
                                else:
                                    with open(config.FEEDBACK_FILE, 'w', encoding='utf-8') as f:
                                        f.writelines(lines[:-30])
                                    reply_content = "已清除最近30条反馈。"
                            except FileNotFoundError:
                                reply_content = "反馈文件不存在，无需清除。"
                    
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
    # 运行 Flask 应用来对接微信
    app.run(host='0.0.0.0', port=80)
