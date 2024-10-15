import os
import platform
import json

def get_user_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'user_config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def process_blender_path(user_path):
    if platform.system() == "Windows":
        # 移除路径两端的引号（如果有的话）
        user_path = user_path.strip('"')
        # 规范化路径
        user_path = os.path.normpath(user_path)
        # 确保路径以 blender.exe 结尾
        if not user_path.lower().endswith('blender.exe'):
            user_path = os.path.join(user_path, 'blender.exe')
        # 验证 blender.exe 是否存在
        if not os.path.exists(user_path):
            print(f"错误：在路径 {user_path} 中未找到 blender.exe")
            return None
        return user_path
    elif platform.system() == "Darwin":  # macOS
        return "/Applications/Blender.app/Contents/MacOS/Blender"
    else:  # Linux
        return user_path  # 假设 Linux 用户提供了正确的路径

def get_blender_path():
    user_config = get_user_config()
    return process_blender_path(user_config['USER_BLENDER_PATH'])

def get_blender_python_path():
    blender_path = get_blender_path()
    if platform.system() == "Darwin":  # macOS
        return os.path.join(os.path.dirname(os.path.dirname(blender_path)), "Resources", "4.2", "python")
    elif platform.system() == "Windows":
        return os.path.join(os.path.dirname(blender_path), "4.2", "python")
    else:  # Linux
        return os.path.join(os.path.dirname(blender_path), "4.2", "python")