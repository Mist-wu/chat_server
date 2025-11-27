import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# CLOUD FLARE 配置
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
AUTH_TOKEN = os.getenv("CLOUDFLARE_AUTH_TOKEN", "")
MODEL = "llama-3.1-8b-instruct-fast"

# 微信验证token
TOKEN = os.getenv("WECHAT_TOKEN", "")

APP_ID = os.getenv("WECHAT_APP_ID", "")
APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")

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

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FEEDBACK_FILE = os.path.join(BASE_DIR, 'user_feedback.txt')