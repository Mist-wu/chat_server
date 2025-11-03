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
        # 使用更健壮的路径拼接
        filepath = os.path.join(os.path.dirname(__file__), 'prompt', filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            persona_prompt = f.read().strip()
            # 身份设定文件内容将覆盖基础指令
            return persona_prompt
    except FileNotFoundError:
        return base_prompt

def get_response(user_id, user_message):
    identity_id = db.get_user_identity(user_id)
    identity_prompt = get_identity_prompt(identity_id)
    
    history = db.get_user_session(user_id)
    if history is None:
        history = []

    # 准备发送给API的消息
    messages_to_send = []
    if identity_prompt:
        messages_to_send.append({"role": "system", "content": identity_prompt})
    
    # 截断历史记录，只保留最近的对话用于发送给API
    # MAX_HISTORY_LEN-1 是因为system prompt占了一个位置
    # 这里我们只取 history 的部分
    if len(history) > (config.MAX_HISTORY_LEN - 1):
        messages_to_send.extend(history[-(config.MAX_HISTORY_LEN - 1):])
    else:
        messages_to_send.extend(history)
    
    # 添加当前用户消息
    messages_to_send.append({"role": "user", "content": user_message})

    ai_response = chat_with_cf(messages_to_send)

    # 如果API调用成功，则更新完整的对话历史
    if not ai_response.startswith(("API返回错误:", "请求失败:", "网络请求异常:")):
        # 将新对话添加到完整的历史记录中
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": ai_response})
        
        # 统一在这里进行截断，以存入数据库
        # 确保数据库中存储的总是最新的 config.MAX_HISTORY_LEN 条消息
        if len(history) > config.MAX_HISTORY_LEN:
             history = history[-config.MAX_HISTORY_LEN:]
        
        db.update_user_session(user_id, history)
    
    return ai_response

def chat_with_cf(messages):
    # 确认配置已正确加载
    if not all([config.ACCOUNT_ID, config.AUTH_TOKEN, config.MODEL]):
        return "网络请求异常: 服务器配置不完整，请联系管理员。"

    API_URL = f"https://api.cloudflare.com/client/v4/accounts/{config.ACCOUNT_ID}/ai/run/@cf/meta/{config.MODEL}"

    headers = {
        "Authorization": f"Bearer {config.AUTH_TOKEN}"
    }
    data = {
        "messages": messages
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=10) # 增加超时时间
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('result'):
                return result['result']['response'].strip() # 清理首尾空格
            else:
                # 记录更详细的日志
                print(f"API Error: {result.get('errors')}")
                return f"API返回错误: {result.get('errors')}"
        else:
            print(f"Request failed: {response.status_code}, {response.text}")
            return f"请求失败: 状态码 {response.status_code}"
    except requests.exceptions.RequestException as e:
        print(f"Network exception: {e}")
        return f"网络请求异常: {e}"
