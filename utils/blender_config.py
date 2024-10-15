import os
import platform
import subprocess
from config import BLENDER_PATH, IS_SERVER

def find_blender_executable(base_path):
    if platform.system() == "Darwin":  # macOS
        return os.path.join(base_path, "Blender")
    elif platform.system() == "Windows":
        return os.path.join(base_path, "blender.exe")
    else:  # Linux or other
        return os.path.join(base_path, "blender")

def find_blender_python_path(blender_path):
    if platform.system() == "Darwin":  # macOS
        resources_path = "/Applications/Blender.app/Contents/Resources"
        # 查找所有以数字开头的目录（这些通常是版本号）
        version_dirs = [d for d in os.listdir(resources_path) if d[0].isdigit()]
        if version_dirs:
            # 选择最新的版本
            latest_version = sorted(version_dirs, key=lambda x: [int(p) for p in x.split('.')])[-1]
            return os.path.join(resources_path, latest_version, "python")
    else:
        blender_dir = os.path.dirname(blender_path)
        for root, dirs, files in os.walk(blender_dir):
            if 'python' in dirs:
                python_path = os.path.join(root, 'python')
                if os.path.isdir(python_path):
                    return python_path
    return None

def set_blender_paths():
    blender_executable = find_blender_executable(BLENDER_PATH)
    
    if not os.path.exists(blender_executable):
        raise FileNotFoundError(f"找不到Blender可执行文件：{blender_executable}")
    
    blender_python_path = find_blender_python_path(blender_executable)
    if not blender_python_path:
        raise FileNotFoundError(f"找不到Blender的Python路径")

    # 验证Blender路径
    try:
        result = subprocess.run([blender_executable, '--version'], capture_output=True, text=True)
        if 'Blender' not in result.stdout:
            raise ValueError("无效的Blender路径")
        print(f"检测到的Blender版本: {result.stdout.strip()}")
    except Exception as e:
        raise ValueError(f"验证Blender路径时出错：{str(e)}")

    return blender_executable, blender_python_path

def get_blender_paths():
    if IS_SERVER:
        # 服务器环境设置
        BLENDER_EXECUTABLE = None
        BLENDER_PYTHON_PATH = None
    else:
        # 本地环境设置
        BLENDER_EXECUTABLE, BLENDER_PYTHON_PATH = set_blender_paths()

    print(f"Blender可执行文件路径：{BLENDER_EXECUTABLE}")
    print(f"Blender Python路径：{BLENDER_PYTHON_PATH}")

    return BLENDER_EXECUTABLE, BLENDER_PYTHON_PATH