# CLOUD FLARE 配置
ACCOUNT_ID = "a100979d641a7b41db7b7cfa3c33d166"
AUTH_TOKEN = ""
MODEL = "llama-3.1-8b-instruct-fast"

# 微信验证token
TOKEN = "mist"

APP_ID = "wx6db309f2190fce40"
APP_SECRET = "b4d14710fd09cab5450046cfe974f8d7"

# 最大历史会话长度
MAX_HISTORY_LEN = 101  # 包含系统指令 + 100条消息

# 管理员用户ID
ADMIN_USER_ID = [
    'oLJUa2F2izQg5s25EBX6dBHwx2YQ',  
]

# 身份配置
# 格式: "编号": {"name": "身份名称", "file": "prompt文件名"}
PERSONAS = {
    "1": {"name": "找人怼你", "file": "chaojia.txt"},
    "2": {"name": "我妻由乃", "file": "Gasai.txt"},
    "3": {"name": "春日野穹", "file": "Kasugano.txt"}
}

FEEDBACK_FILE = 'user_feedback.txt'
