import requests
import json
import config # 导入你的配置文件

def get_access_token():
    """
    获取微信全局接口的 access_token
    """
    # 从配置文件中读取 AppID 和 AppSecret
    app_id = config.APP_ID
    app_secret = config.APP_SECRET

    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # 如果请求失败（非200状态码），则抛出异常
        
        result = response.json()
        
        if "access_token" in result:
            print(f"成功获取 access_token，有效期至：{result['expires_in']} 秒")
            return result['access_token']
        else:
            print(f"获取 access_token 失败：{result}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"请求 access_token 时发生网络错误: {e}")
        return None

def create_menu(access_token):
    """
    使用 access_token 创建自定义菜单
    """
    url = f"https://api.weixin.qq.com/cgi-bin/menu/create?access_token={access_token}"
    
    # --- 在这里定义你的菜单结构 ---
    # type: click -> 用户点击后，微信服务器会向你的后台发送一条消息，内容为 key 的值
    # type: view  -> 用户点击后，会跳转到 url 指定的网页
    menu_data = {
        "button": [
            {
                "name": "指令帮助",
                "type": "click",
                "key": "/指令"  # 对应你项目中的指令
            },
            {
                "name": "功能",
                "sub_button": [
                    {
                        "name": "查天气",
                        "type": "click",
                        "key": "/天气 北京" # 示例，用户点击后会发送"/天气 北京"
                    },
                    {
                        "name": "清空历史",
                        "type": "click",
                        "key": "/清空历史"
                    },
                    {
                        "name": "我的博客", # 示例：跳转网页
                        "type": "view",
                        "url": "http://blog.qbsdw.me/" # 请替换成你的博客或其他链接
                    }
                ]
            }
        ]
    }
    # ---------------------------------

    # requests post请求不能直接传dict，需要先转换成json字符串
    # 同时，为了正确处理中文，需要指定 ensure_ascii=False
    menu_json = json.dumps(menu_data, ensure_ascii=False).encode('utf-8')
    
    try:
        response = requests.post(url, data=menu_json)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("errcode") == 0:
            print("自定义菜单创建成功！")
        else:
            print(f"自定义菜单创建失败：{result}")
            
    except requests.exceptions.RequestException as e:
        print(f"创建菜单时发生网络错误: {e}")

if __name__ == '__main__':
    print("开始创建自定义菜单...")
    token = get_access_token()
    if token:
        create_menu(token)
    else:
        print("因未能获取 access_token，菜单创建中止。")