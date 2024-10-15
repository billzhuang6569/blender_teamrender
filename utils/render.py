import subprocess
import os
import sys
import json
import argparse
import platform
import logging
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BLENDER_PATH, BLENDER_PYTHON_PATH
from utils.get_render_settings import get_render_settings

# Import logging for error handling
import logging

def render_blender(blend_file, output_dir, start_frame, end_frame):
    # 获取当前工作目录的绝对路径
    current_dir = os.path.abspath(os.getcwd())
    
    # 构建绝对路径
    blend_file_abs = os.path.join(current_dir, blend_file)
    output_dir_abs = os.path.join(current_dir, output_dir)
    
    # 确保输出目录存在
    os.makedirs(output_dir_abs, exist_ok=True)
    # 构建 Blender 命令，使用绝对路径
    cmd = [
        BLENDER_PATH,
        "-b",
        blend_file_abs,
        "-o", os.path.join(output_dir_abs, "frame_####"),
        "-s", str(start_frame),
        "-e", str(end_frame),
        "-a"
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logging.info(result.stdout)
        
        # 检查是否所有指定的帧都已渲染
        rendered_frames = [f for f in os.listdir(output_dir_abs) if f.startswith("frame_") and f.endswith(".png")]
        rendered_frame_numbers = [int(f.split("_")[1].split(".")[0]) for f in rendered_frames]
        
        if rendered_frame_numbers:
            return max(rendered_frame_numbers)
        else:
            logging.warning("No frames were rendered")
            return start_frame - 1
    except subprocess.CalledProcessError as e:
        logging.error(f"Rendering error: {e}")
        logging.error(e.stdout)
        logging.error(e.stderr)
        return str(e)
    except Exception as e:
        logging.error(f"Unexpected error during rendering: {str(e)}")
        return str(e)

def get_blend_file_settings(blend_file):
    settings = get_render_settings(blend_file)
    return settings

def main():
    parser = argparse.ArgumentParser(description="使用Blender命令行进行渲染")
    parser.add_argument("blend_file", help="要渲染的.blend文件路径")
    parser.add_argument("output_dir", help="渲染输出目录")
    parser.add_argument("start_frame", type=int, help="起始帧")
    parser.add_argument("end_frame", type=int, help="结束帧")
    
    args = parser.parse_args()
    
    result = render_blender(args.blend_file, args.output_dir, args.start_frame, args.end_frame)
    if isinstance(result, int):
        print(f"渲染成功完成，最后渲染的帧是：{result}")
    else:
        print(f"渲染失败，错误信息：{result}")

if __name__ == "__main__":
    main()
