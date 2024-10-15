import json
import os
import subprocess
import logging
from config import BLENDER_PATH, IS_SERVER
import sys

def get_render_settings(blend_file_path, room_id):
    script = """
import bpy
import json

# 禁用所有插件
for addon in bpy.context.preferences.addons.keys():
    bpy.ops.preferences.addon_disable(module=addon)

scene = bpy.context.scene
render = scene.render

settings = {
    "renderer": render.engine,
    "start_frame": scene.frame_start,
    "end_frame": scene.frame_end,
    "resolution_x": render.resolution_x,
    "resolution_y": render.resolution_y,
    "resolution_percentage": render.resolution_percentage,
    "file_format": render.image_settings.file_format
}

print("RENDER_SETTINGS_START")
print(json.dumps(settings))
print("RENDER_SETTINGS_END")
"""

    result = subprocess.run(
        [BLENDER_PATH, "-b", blend_file_path, "--python-expr", script],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logging.error(f"Blender execution failed: {result.stderr}")
        raise ValueError("Failed to get render settings from Blender")

    # 从输出中提取 JSON 数据
    output = result.stdout
    print("Blender的原始output: ", output)
    start_marker = "RENDER_SETTINGS_START"
    end_marker = "RENDER_SETTINGS_END"
    
    start_index = output.find(start_marker)
    end_index = output.find(end_marker)
    
    if start_index == -1 or end_index == -1:
        logging.error(f"Failed to find JSON data in Blender output: {output}")
        raise ValueError("Failed to extract render settings from Blender output")
    
    json_data = output[start_index + len(start_marker):end_index].strip()
    
    try:
        settings = json.loads(json_data)
        return settings
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON data: {json_data}")
        logging.error(f"JSON decode error: {str(e)}")
        raise ValueError("Failed to parse render settings JSON")

def save_render_settings(room_id, settings):
    log_dir = os.path.join("render", room_id, "log")
    os.makedirs(log_dir, exist_ok=True)
    settings_file = os.path.join(log_dir, "render_settings.json")
    
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)

if __name__ == "__main__":
    # 获取传入的 .blend 文件路径
    blend_file = sys.argv[1] if len(sys.argv) > 1 else None

    if not blend_file:
        print("请提供 .blend 文件路径")
        sys.exit(1)

    # 获取渲染设置
    settings = get_render_settings(blend_file)

    # 将设置输出为 JSON 格式
    print(json.dumps(settings, indent=2))