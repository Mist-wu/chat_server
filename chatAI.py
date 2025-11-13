import config
import requests
import os
import database as db
import weather  # 导入天气模块
import re # 导入正则表达式模块

    
def get_identity_prompt(identity_id):
    """根据身份ID获取对应的prompt内容。"""
    base_prompt = "你是一个名为'驱不散的雾'的AI助手。你的任务是友好、简洁地回答用户的问题。请始终使用简体中文回复。回复应像真人聊天，通常不超过30字，除非用户要求详细解释。"

    if identity_id == 0:
        return base_prompt

    persona = config.PERSONAS.get(str(identity_id))
    if not persona: 
        return base_prompt

    filename = persona.get("file")
    if not filename:
        return base_prompt

    try:
        filepath = os.path.join(os.path.dirname(__file__), 'prompt', filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            persona_prompt = f.read().strip()
            return persona_prompt
    except FileNotFoundError:
        return base_prompt

def get_weather_report(city):
    """获取并格式化天气报告。"""
    weather_data = weather.get_weather(city)
    if weather_data:
        city_name = weather_data['city']
        temp = weather_data['temp']
        weather_type = weather_data['weather_type']
        wind = weather_data['wind']
        return f"今日{city_name}的天气是{weather_type}，温度是{temp}，有{wind}。"
    return None

def get_response(user_id, user_message):
    """获取AI回复，并管理会话历史。"""
    
    # 1. 检查是否有待处理的动作
    pending_action = db.get_user_setting(user_id, 'pending_action')
    if pending_action == 'awaiting_city_for_weather':
        # 用户回复了城市名，直接查天气
        report = get_weather_report(user_message.strip())
        db.update_user_setting(user_id, 'pending_action', None) # 清除状态
        if report:
            # 天气查询成功，不计入历史，直接返回结果
            return report
        # 如果用户回复的不是城市名，或者查不到，则继续走标准流程

    # 2. 检查用户是否在问天气
    weather_keywords = ['天气', '气温', '温度']
    if any(keyword in user_message for keyword in weather_keywords):
        # 尝试从消息中提取城市名 (例如 "北京天气怎么样" or "查一下北京的天气")
        all_cities = weather.get_all_cities() # 获取所有支持的城市列表
        found_city = None
        for city in all_cities:
            if city in user_message:
                found_city = city
                break
        
        if found_city:
            # 找到了城市，直接查询并返回天气
            report = get_weather_report(found_city)
            if report:
                # 天气查询成功，不计入历史，直接返回结果
                return report
        else:
            # 没找到城市，向用户提问，并直接返回
            db.update_user_setting(user_id, 'pending_action', 'awaiting_city_for_weather')
            return "好的，请问您想查询哪里的天气？"

    # 3. 如果以上都不是，则走标准聊天流程
    identity_id = db.get_user_identity(user_id)
    identity_prompt = get_identity_prompt(identity_id)
    
    history = db.get_user_session(user_id) or []
    messages_to_send = [{"role": "system", "content": identity_prompt}]
    
    history_for_api = history[-(config.MAX_HISTORY_LEN - 1):]
    messages_to_send.extend(history_for_api)
    
    messages_to_send.append({"role": "user", "content": user_message})

    ai_response = chat_with_cf(messages_to_send)

    if ai_response and not ai_response.startswith(("API返回错误:", "请求失败:", "网络请求异常:")):
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": ai_response})
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
        response = requests.post(API_URL, headers=headers, json=data, timeout=20)
        response.raise_for_status()

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