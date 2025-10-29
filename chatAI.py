import config
import requests
import os
import database as db

    
def get_identity_prompt(identity_id):
    """根据身份ID获取对应的prompt内容。"""
    # 基础指令，确保语言和格式
    base_prompt = "你必须始终使用简体中文进行回复，像真人聊天一样回复我，回复不要超过30字。"

    if identity_id == 0:
        return base_prompt  # 默认身份也应用基础指令

    persona = config.PERSONAS.get(str(identity_id))
    if not persona: 
        return base_prompt

    filename = persona.get("file")
    if not filename:
        return base_prompt

    try:
        filepath = os.path.join('prompt', filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            persona_prompt = f.read().strip()
            return f"{base_prompt}\n\n{persona_prompt}"
    except FileNotFoundError:
        return base_prompt

def get_response(user_id, user_message):
    identity_id = db.get_user_identity(user_id)
    identity_prompt = get_identity_prompt(identity_id)
    
    history = db.get_user_session(user_id)
    if history is None:
        history = []

    # 将身份prompt作为系统消息添加到对话历史的开头
    messages = []
    if identity_prompt:
        messages.append({"role": "system", "content": identity_prompt})
    
    # 添加历史对话
    messages.extend(history)
    
    # 添加当前用户消息
    messages.append({"role": "user", "content": user_message})

    ai_response = chat_with_cf(messages)

    # 更新对话历史
    if not ai_response.startswith(("API返回错误:", "请求失败:", "网络请求异常:")):
        # 更新对话历史
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": ai_response})
        db.update_user_session(user_id, history)
    
    return ai_response

def chat_with_cf(messages):
    ACCOUNT_ID = config.ACCOUNT_ID
    AUTH_TOKEN = config.AUTH_TOKEN
    API_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/meta/llama-3.1-8b-instruct-fast"

    headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    data = {
        "messages": messages
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('result'):
                return result['result']['response']
            else:
                return f"API返回错误: {result.get('errors')}"
        else:
            return f"请求失败: {response.status_code}, {response.text}"
    except requests.exceptions.RequestException as e:
        return f"网络请求异常: {e}"