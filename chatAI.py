import config
import requests
import os
import database as db

    
def get_identity_prompt(identity_id):
    """根据身份ID获取对应的prompt内容。"""
    # 基础指令，确保语言和格式
    base_prompt = "你是一个名为'驱不散的雾'的AI助手。你的任务是友好、简洁地回答用户的问题。请始终使用简体中文回复。回复应像真人聊天，通常不超过30字，除非用户要求详细解释。"

    if identity_id == 0:
        return base_prompt  # 默认身份

    persona = config.PERSONAS.get(str(identity_id))
    if not persona: 
        return base_prompt

    filename = persona.get("file")
    if not filename:
        return base_prompt

    try:
        # 使用更健壮的路径拼接
        filepath = os.path.join(os.path.dirname(__file__), 'prompt', filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            persona_prompt = f.read().strip()
            # 对于有复杂设定的prompt，直接使用文件内容，不再拼接base_prompt
            return persona_prompt
    except FileNotFoundError:
        return base_prompt

def get_response(user_id, user_message):
    """获取AI回复，并管理会话历史。"""
    identity_id = db.get_user_identity(user_id)
    identity_prompt = get_identity_prompt(identity_id)
    
    # 使用 'or []' 使代码更简洁
    history = db.get_user_session(user_id) or []

    # 准备发送给API的消息
    messages_to_send = [{"role": "system", "content": identity_prompt}]
    
    # 统一在这里截取需要发送给API的历史记录
    # -1 是为了给 system prompt 留出位置
    history_for_api = history[-(config.MAX_HISTORY_LEN - 1):]
    messages_to_send.extend(history_for_api)
    
    # 添加当前用户消息
    messages_to_send.append({"role": "user", "content": user_message})

    ai_response = chat_with_cf(messages_to_send)

    # 仅当API调用成功时才更新历史记录
    if ai_response and not ai_response.startswith(("API返回错误:", "请求失败:", "网络请求异常:")):
        # 将新对话添加到完整的历史记录中
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": ai_response})
        
        # 存入数据库前，进行最终截断，确保数据库中的历史记录不会超过设定的最大值
        # 注意：这里我们截断的是包含用户新消息和AI回复的完整历史
        final_history_to_save = history[-config.MAX_HISTORY_LEN:]
        
        db.update_user_session(user_id, final_history_to_save)
    
    return ai_response

def chat_with_cf(messages):
    """调用Cloudflare AI API。"""
    if not all([config.ACCOUNT_ID, config.AUTH_TOKEN, config.MODEL]):
        return "网络请求异常: 服务器配置不完整，请联系管理员。"

    API_URL = f"https://api.cloudflare.com/client/v4/accounts/{config.ACCOUNT_ID}/ai/run/@cf/meta/{config.MODEL}"

    headers = {"Authorization": f"Bearer {config.AUTH_TOKEN}"}
    data = {"messages": messages}

    try:
        # 增加超时时间和异常处理
        response = requests.post(API_URL, headers=headers, json=data, timeout=20)
        response.raise_for_status()  # 如果状态码不是 2xx，则抛出异常

        result = response.json()
        if result.get('success') and result.get('result'):
            return result['result']['response'].strip()
        else:
            error_details = result.get('errors') or result.get('messages', '未知API错误')
            print(f"API Error: {error_details}")
            return f"API返回错误: {error_details}"
            
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code}, {e.response.text}")
        return f"请求失败: 状态码 {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        print(f"Network exception: {e}")
        return f"网络请求异常: {e}"
