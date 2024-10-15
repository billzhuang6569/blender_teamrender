import gradio as gr
import os
import json
import requests
import zipfile
import io
from datetime import datetime
from client import create_room, join_room, trigger_rendering, start_rendering, download_render_results, get_client_id, BASE_URL, upload_blend_file, render_loop
import time
import logging
import threading
import platform
import socket
import psutil

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加一个全局变量来存储渲染状态
render_status = {"completed": False}

# 新增函数：检查端口是否被占用
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# 在启动 Gradio 之前检查端口
def prepare_ports():
    ports_to_check = [7860, 7861]
    for port in ports_to_check:
        if is_port_in_use(port):
            logger.warning(f"Port {port} is already in use. Please ensure it's free before starting the application.")
        else:
            logger.info(f"Port {port} is available.")

def load_room_info(room_id):
    room_settings_path = f"./render/{room_id}/log/room_settings.json"
    if os.path.exists(room_settings_path):
        with open(room_settings_path, 'r') as f:
            return json.load(f)
    return None

def format_room_info(room_info, room_id, client_id):
    if not room_info:
        return f"🏠 房间ID: {room_id}\n👤 客户端ID: {client_id}\n🚦 状态: 等待中"
    
    info_str = f"🏠 房间ID: {room_info.get('room_id', room_id)}\n"
    info_str += f"👤 客户端ID: {client_id}\n"
    if 'members' in room_info and room_info['members']:
        info_str += f"👥 创建者ID: {room_info['members'][0].get('id', '未知')}\n"
    info_str += f"🚦 状态: {room_info.get('status', '未知')}\n"
    info_str += f"🕒 创建时间: {room_info.get('create_time', '未知')}"
    return info_str

def load_tasks(room_id):
    tasks_path = f"./render/{room_id}/log/tasks.json"
    if os.path.exists(tasks_path):
        with open(tasks_path, 'r') as f:
            return json.load(f)
    return []

def format_tasks(tasks):
    if not tasks:
        return "📭 没有可用的任务。"
    
    tasks_str = "📋 任务列表:\n"
    for task in tasks:
        tasks_str += f"🔹 ID: {task['id']}, 状态: {task['status']}, 帧范围: {task['start_frame']}-{task['end_frame']}\n"
    return tasks_str

def create_or_join_room(action, room_id_input=None):
    client_id = get_client_id()
    if action == "Create":
        room_id, client_id = create_room()
    else:
        room_id, client_id, res_json = join_room(room_id_input)
    
    if room_id:
        room_info = load_room_info(room_id)
        tasks = load_tasks(room_id)
        return (
            f"✅ 成功{'创建' if action == 'Create' else '加入'}房间 {room_id}",
            gr.update(visible=True),
            format_room_info(room_info, room_id, client_id),
            format_tasks(tasks),
            room_id,
            client_id
        )
    else:
        return f"❌ 无法{'创建' if action == 'Create' else '加入'}房间", gr.update(visible=False), "", "", "", ""

def trigger_render(room_id):
    trigger_rendering(room_id)
    tasks = load_tasks(room_id)
    return f"🚀 房间 {room_id} 的渲染已触发", format_tasks(tasks)

def start_render(room_id, client_id):
    if start_rendering(room_id):
        tasks = load_tasks(room_id)
        current_task = next((task for task in tasks if task['status'] == 'triggered'), None)
        if current_task:
            task_info = f"任务ID: {current_task['id']}, 帧范围: {current_task['start_frame']}-{current_task['end_frame']}"
        else:
            task_info = "无可用任务"
        
        # 启动一个后台线程来执行渲染
        def render_thread():
            render_loop(room_id, client_id)
            render_status["completed"] = True
        
        threading.Thread(target=render_thread).start()
        
        return f"🎬 房间 {room_id} 的渲染已开始，当前任务：{task_info}", "渲染已开始，等待进度更新..."
    else:
        return "❌ 无法开始渲染", "渲染未开始"

def check_room_status(room_id):
    room_info = load_room_info(room_id)
    tasks = load_tasks(room_id)
    return format_room_info(room_info, room_id, get_client_id()), format_tasks(tasks)

def upload_files(room_id, files):
    if not room_id:
        return "⚠️ 请先创建或加入一个房间。"
    
    results = []
    for file in files:
        if file.name.endswith('.blend'):
            result = upload_blend_file(room_id, file.name)
            if result:
                results.append(f"✅ {os.path.basename(file.name)} 上传成功！")
            else:
                results.append(f"❌ {os.path.basename(file.name)} 上传失败。")
        else:
            results.append(f"⏭️ {os.path.basename(file.name)} 已跳过（不是 .blend 文件）")
    
    return "\n".join(results)

def get_render_results(room_id):
    download_render_results(room_id)
    final_dir = os.path.join("render", room_id, "final")
    if os.path.exists(final_dir):
        files = [os.path.join(final_dir, f) for f in os.listdir(final_dir) if os.path.isfile(os.path.join(final_dir, f))]
        return gr.update(value=files, visible=True)
    else:
        return gr.update(value=None, visible=False)

def create_zip_file(room_id):
    final_dir = os.path.join("render", room_id, "final")
    zip_dir = os.path.join("render", room_id, "zip")
    os.makedirs(zip_dir, exist_ok=True)
    zip_path = os.path.join(zip_dir, f"all_results_{room_id}.zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(final_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, final_dir)
                zipf.write(file_path, arcname)
    
    return zip_path

def download_all_results(room_id):
    # 首先执行下载渲染结果
    result = download_render_results(room_id)
    if result['result'] == 'done':
        # 创建 ZIP 文件
        zip_path = create_zip_file(room_id)
        return gr.File(value=zip_path, visible=True), f"所有渲染任务已完成。ZIP 文件已创建：{zip_path}"
    else:
        missing_tasks = result.get('missing', {})
        if missing_tasks:
            missing_info = ", ".join([f"任务 {task_id}: {status}" for task_id, status in missing_tasks.items()])
            return gr.File(value=None, visible=False), f"部分任务未完成。未完成的任务：{missing_info}"
        else:
            return gr.File(value=None, visible=False), "无法创建 ZIP 文件。请检查渲染结果。"

def update_render_progress(room_id, progress, current_task, current_frame):
    return f"渲染进度: {progress:.2f}%, 当前任务: {current_task}, 前帧: {current_frame}"

def check_render_status(room_id):
    response = requests.get(f"{BASE_URL}/get_tasks", params={"room_id": room_id})
    if response.status_code == 200:
        tasks = response.json()["tasks"]
        all_completed = all(task["status"] in ["done", "failed"] for task in tasks)
        if all_completed:
            return "🎉 所有渲染任务已完成！"
        else:
            in_progress = sum(1 for task in tasks if task["status"] == "rendering")
            completed = sum(1 for task in tasks if task["status"] in ["done", "failed"])
            total = len(tasks)
            return f"渲染进行中... {completed}/{total} 任务完成，{in_progress} 任务进行中"
    return "无法获取渲染状态"

def update_render_progress(room_id):
    status = check_render_status(room_id)
    return status

def load_user_config():
    try:
        with open('user_config.json', 'r') as f:
            config = json.load(f)
        return {
            "username": config.get("client_id", ""),
            "blender_path": config.get("USER_BLENDER_PATH", ""),
            "server_ip": config.get("SERVER_IP", ""),
            "server_port": config.get("SERVER_PORT", "")
        }
    except FileNotFoundError:
        return {"username": "", "blender_path": "", "server_ip": "", "server_port": ""}

def save_user_config(username, blender_path, server_ip, server_port):
    config = {
        "client_id": username,
        "USER_BLENDER_PATH": blender_path,
        "SERVER_IP": server_ip,
        "SERVER_PORT": server_port,
        "UPLOAD_FOLDER": "/usr/teamrender/upload",
        "ROOMS_FOLDER": "/usr/teamrender/rooms"
    }
    with open('user_config.json', 'w') as f:
        json.dump(config, f, indent=4)
    return "✅ 设置已保存"

# 主程序
if __name__ == "__main__":
    prepare_ports()  # 在创建 Gradio 界面之前调用此函数

    with gr.Blocks() as demo:
        gr.Markdown("# 🎨 Blender 协作渲染平台")
        
        with gr.Row():
            with gr.Column(scale=2):
                with gr.Row():
                    create_btn = gr.Button("🆕 创建新房间")
                    join_btn = gr.Button("🔗 加入已有房间")
                    room_id_input = gr.Textbox(label="房间 ID")
                
                room_actions = gr.Column(visible=False)
                with room_actions:
                    file_upload = gr.File(label="选择 Blender 文件（可多选）", file_count="multiple")
                    upload_btn = gr.Button("📤 上传选中的文件")
                    trigger_btn = gr.Button("📊 分配任务")
                    start_btn = gr.Button("▶️ 开始渲染")
                    check_status_btn = gr.Button("🔄 刷新任务列表")
                    download_btn = gr.Button("📥 下载渲染结果")
                    download_all_btn = gr.Button("📦 打包所有结果")
                
                output = gr.Textbox(label="系统消息", lines=5)
                
                room_info = gr.Textbox(label="房间信息", lines=10)
                tasks_info = gr.Textbox(label="任务列表", lines=10)
                
                render_results = gr.File(label="渲染结果", visible=False, file_count="multiple")
                all_results_zip = gr.File(label="打包结果 (ZIP)", visible=False)
                download_status_text = gr.Textbox(label="载状态", visible=False)
            
            # 设置面板直接显示在右侧
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ 设置")
                config = load_user_config()
                username = gr.Textbox(label="用户名", info="唯一标识您身份的名称", value=config["username"])
                
                # 根据操作系统决定是否显示 Blender 路径设置
                if platform.system() == "Windows":
                    blender_path = gr.Textbox(label="Blender路径", info="Windows用户必须填写", value=config["blender_path"])
                else:
                    blender_path = gr.State(value="")  # 使用 gr.State 来存储空值，但不显示在界面上
                
                server_ip = gr.Textbox(label="服务器IP", info="非自部署情况下，勿动", value=config["server_ip"])
                server_port = gr.Number(label="服务器端口", info="非自部署情况下，勿动", value=config["server_port"])
                save_btn = gr.Button("💾 保存设置")
        
        current_room_id = gr.State("")
        current_client_id = gr.State("")

        # 事件处理代码保持不变
        create_btn.click(lambda: create_or_join_room("Create", None), outputs=[output, room_actions, room_info, tasks_info, current_room_id, current_client_id])
        join_btn.click(lambda x: create_or_join_room("Join", x), inputs=[room_id_input], outputs=[output, room_actions, room_info, tasks_info, current_room_id, current_client_id])
        
        upload_btn.click(upload_files, inputs=[current_room_id, file_upload], outputs=[output])
        trigger_btn.click(trigger_render, inputs=[current_room_id], outputs=[output, tasks_info])
        start_btn.click(start_render, inputs=[current_room_id, current_client_id], outputs=[output])
        check_status_btn.click(check_room_status, inputs=[current_room_id], outputs=[room_info, tasks_info])
        download_btn.click(get_render_results, inputs=[current_room_id], outputs=[render_results])
        download_all_btn.click(download_all_results, inputs=[current_room_id], outputs=[all_results_zip, download_status_text])
        
        save_btn.click(
            save_user_config,
            inputs=[username, blender_path, server_ip, server_port],
            outputs=[output]
        )

        # update_status 函数和 start_render_with_updates 函数保持不变
        def update_status(room_id, client_id):
            if room_id:
                room_info, tasks_info = check_room_status(room_id)
                render_results = get_render_results(room_id)
                
                if render_status["completed"]:
                    render_status_text = "🎉 所有渲染任务已完成！"
                    render_status["completed"] = False
                else:
                    render_status_text = "渲染进行中..."
                
                return room_info, tasks_info, render_results, render_status_text
            return "", "", gr.update(value=None, visible=False), "等待开始渲染"

        demo.load(update_status, inputs=[current_room_id, current_client_id], outputs=[room_info, tasks_info, render_results, download_status_text])

        def start_render_with_updates(room_id, client_id):
            if start_rendering(room_id):
                threading.Thread(target=render_loop, args=(room_id, client_id)).start()
                return "渲染已开始，请等待更新..."
            else:
                return "无法开始渲染"

        start_btn.click(start_render_with_updates, inputs=[current_room_id, current_client_id], outputs=[download_status_text])

    demo.queue()
    demo.launch(server_port=7860)  # 指定使用 7860 端口