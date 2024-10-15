import json
import os
import platform
from utils.path_utils import get_blender_path, get_blender_python_path

# 读取用户配置
config_path = os.path.join(os.path.dirname(__file__), 'user_config.json')
with open(config_path, 'r') as f:
    user_config = json.load(f)

# 服务器设置
server_ip = user_config['SERVER_IP']
server_port = user_config['SERVER_PORT']

# 判断是否在服务器环境
IS_SERVER = platform.system() == "Linux"  # 假设服务器运行在 Linux 上

# 从用户配置中读取文件夹路径
UPLOAD_FOLDER = user_config['UPLOAD_FOLDER']
ROOMS_FOLDER = user_config['ROOMS_FOLDER']

# CONFIG程序处理
BLENDER_PATH = get_blender_path()
BLENDER_PYTHON_PATH = get_blender_python_path()


