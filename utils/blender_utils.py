import os

def get_blender_python_path(blender_path):
    base_path = os.path.dirname(os.path.dirname(blender_path))
    resources_path = os.path.join(base_path, "Resources")
    
    # 查找最新版本的 Blender Python
    versions = [d for d in os.listdir(resources_path) if d[0].isdigit()]
    if not versions:
        raise ValueError("无法找到 Blender Python 路径")
    
    latest_version = max(versions)
    python_path = os.path.join(resources_path, latest_version, "python", "lib")
    
    # 查找 Python 版本
    python_versions = [d for d in os.listdir(python_path) if d.startswith("python3")]
    if not python_versions:
        raise ValueError("无法找到 Python 版本")
    
    latest_python = max(python_versions)
    
    return os.path.join(python_path, latest_python)