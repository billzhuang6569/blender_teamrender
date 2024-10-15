import sys
import json
import os
import requests
import time
import shutil
import platform
import logging
import zipfile
import random
from datetime import datetime
from config import server_ip, server_port, BLENDER_PATH
from utils.render import render_blender
from requests.exceptions import RequestException
from utils.get_render_settings import get_render_settings, save_render_settings
from utils.file_transfer import upload_file, download_file

BASE_URL = f"http://{server_ip}:{server_port}"

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_logging(room_id):
    log_dir = os.path.join("render", room_id, "log")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"client_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def create_room(room_id=None):
    if room_id is None:
        room_id = f"{random.randint(100000, 999999)}"  # 生成一个随机的6位数字
    client_id = get_client_id()
    response = requests.post(f"{BASE_URL}/create_room", json={"room_id": room_id, "client_id": client_id})
    if response.status_code == 200:
        logging.info(f"房间 {room_id} 创建成功")
        create_local_room_structure(room_id)
        
        # 下载 room_settings.json
        download_room_settings(room_id)
        
        return room_id, client_id
    else:
        logging.error(f"创建房间失败: {response.text}")
        return None, None

def join_room(room_id):
    client_id = get_client_id()
    response = requests.post(f"{BASE_URL}/join_room", json={"room_id": room_id, "client_id": client_id})
    if response.status_code == 200:
        print(f"Joined room {room_id}")
        create_local_room_structure(room_id)
        # 下载 room_settings.json
        download_room_settings(room_id)
        print(f"room_id: {room_id}, client_id: {client_id}, response: {response.json()}")
        return room_id, client_id, response.json()
        
    else:
        print("Failed to join room")
        return None, None, None

def create_local_room_structure(room_id):
    base_path = os.path.join("render", room_id)
    os.makedirs(os.path.join(base_path, "queue"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "results"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "log"), exist_ok=True)  # 添加这行

def upload_blend_file(room_id, blend_file_path):
    # 检查房间状态
    status = get_room_status(room_id)
    if status is None:
        print("Unable to get room status. Aborting upload.")
        return False
    
    if status.get('status') != 'waiting':
        print(f"Room is not in waiting status. Current status: {status.get('status')}. Cannot upload files.")
        return False

    # 复制 Blender 文件到本地队列
    local_queue_dir = os.path.join("render", room_id, "queue")
    os.makedirs(local_queue_dir, exist_ok=True)
    local_blend_file = os.path.join(local_queue_dir, os.path.basename(blend_file_path))
    shutil.copy(blend_file_path, local_blend_file)

    # 获取渲染设置
    settings = get_render_settings(local_blend_file, room_id)  # 添加 room_id 参数
    
    # 更新本地 render_settings.json
    render_settings_path = os.path.join("render", room_id, "log", "render_settings.json")
    if os.path.exists(render_settings_path):
        with open(render_settings_path, 'r') as f:
            render_settings = json.load(f)
    else:
        render_settings = {}
    
    file_name = os.path.basename(local_blend_file)
    render_settings[file_name] = settings
    
    with open(render_settings_path, 'w') as f:
        json.dump(render_settings, f, indent=2)

    print(f"上传 Blender 文和渲染设置到服务器: {local_blend_file}, {render_settings_path}")
    print(f"房间号: {room_id}")
    # 上传 Blender 文和渲染设置到服务器
    success = upload_file(local_blend_file, f"{BASE_URL}/upload", data={"room_id": room_id})
    if not success:
        print("Failed to upload Blender file")
        return False

    success = upload_file(render_settings_path, f"{BASE_URL}/upload", data={"room_id": room_id})
    if not success:
        print("Failed to upload render settings")
        return False

    # 添加这个新的 API 调用
    response = requests.post(f"{BASE_URL}/add_blend_file", json={
        "room_id": room_id,
        "file_path": os.path.basename(blend_file_path)
    })
    if response.status_code != 200:
        print(f"Failed to add Blender file to room settings: {response.text}")
        return False

    print("Blend file and render settings uploaded successfully")
    download_room_settings(room_id)  # 更新 room_settings.json
    return True

def trigger_rendering(room_id):
    response = requests.post(f"{BASE_URL}/trigger_rendering", json={"room_id": room_id})
    if response.status_code == 200:
        print("Rendering triggered successfully")
        # 添加下载 tasks.json 的代码
        download_tasks(room_id)
        return True
    else:
        print(f"Failed to trigger rendering: {response.text}")
        return False

def download_tasks(room_id):
    url = f"{BASE_URL}/download_tasks?room_id={room_id}"
    local_path = f"./render/{room_id}/log/tasks.json"
    success = download_file(url, local_path)
    if success:
        print(f"Successfully downloaded tasks.json to {local_path}")
    else:
        print(f"Failed to download tasks.json")

def get_room_settings(room_id):
    response = requests.get(f"{BASE_URL}/download_room_settings", params={"room_id": room_id})
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get room settings. Status code: {response.status_code}")
        return None

def start_rendering(room_id):
    response = requests.post(f"{BASE_URL}/start_rendering", json={"room_id": room_id})
    if response.status_code == 200:
        print("Rendering started")
        download_room_settings(room_id)  # 更新 room_settings.json
        return True
    else:
        print(f"Failed to start rendering. Status code: {response.status_code}")
        print(f"Error message: {response.text}")
        return False

# 添加一个新数来处理Blender路
def get_blender_path():
    if platform.system() == "Windows":
        return os.path.join(BLENDER_PATH, "blender.exe")
    else:
        return BLENDER_PATH

# 修改render_task函数
def render_task(room_id, task, client_id):
    blend_file = os.path.join("render", room_id, "queue", os.path.basename(task['file']))
    output_dir = os.path.join("render", room_id, "results", task['id'])
    
    logging.info(f"Rendering {blend_file} frames {task['start_frame']}-{task['end_frame']} to {output_dir}")
    
    result = render_blender(blend_file, output_dir, task['start_frame'], task['end_frame'])
    
    if isinstance(result, int):
        logging.info(f"Rendering completed. Last frame rendered: {result}")
        for frame in range(task['start_frame'], min(result, task['end_frame']) + 1):
            frame_info = {
                "frame": frame,
                "task_id": task['id'],
                "client": client_id,
                "blend_file": os.path.basename(task['file'])
            }
            try:
                response = requests.post(f"{BASE_URL}/update_render_log", json={"room_id": room_id, "frame_info": frame_info})
                response.raise_for_status()
            except requests.RequestException as e:
                logging.error(f"Failed to update render log: {e}")
        return True
    else:
        logging.error(f"Rendering failed: {result}")
        return False

# 添加一个新函数来下载Blender文件
def download_blend_file(room_id, file_path):
    file_name = os.path.basename(file_path)
    local_path = os.path.join("render", room_id, "queue", file_name)
    
    url = f"{BASE_URL}/download_blend_file?room_id={room_id}&file_path={file_path}"
    logging.info(f"Attempting to download from: {url}")
    
    try:
        success = download_file(url, local_path)
        if success:
            logging.info(f"Downloaded Blender file to {local_path}")
            return True
        else:
            logging.error(f"Failed to download Blender file from {url}")
            return False
    except Exception as e:
        logging.error(f"Error downloading Blender file: {str(e)}")
        return False

def organize_results(room_id):
    response = requests.get(f"{BASE_URL}/get_render_log", params={"room_id": room_id})
    if response.status_code == 200:
        render_log = response.json()
        blend_files = set(entry["blend_file"] for entry in render_log)
        
        for blend_file in blend_files:
            output_dir = os.path.join("render", room_id, "render", blend_file.replace(".blend", ""))
            os.makedirs(output_dir, exist_ok=True)
            
            for entry in render_log:
                if entry["blend_file"] == blend_file:
                    src = os.path.join("render", room_id, "results", entry["task_id"], f"frame_{entry['frame']:04d}.png")
                    dst = os.path.join(output_dir, f"frame_{entry['frame']:04d}.png")
                    if os.path.exists(src):
                        shutil.move(src, dst)
        
        print(f"Results organized for room {room_id}")
    else:
        print("Failed to get render log")

def upload_results(room_id, task):
    results_dir = os.path.join("render", room_id, "results", task['id'])
    for file in os.listdir(results_dir):
        file_path = os.path.join(results_dir, file)
        retries = 3
        while retries > 0:
            if upload_file(file_path, f"{BASE_URL}/upload_result", data={"room_id": room_id, "task_id": task['id']}):
                print(f"Uploaded {file}")
                break
            else:
                print(f"Failed to upload {file}")
            
            retries -= 1
            if retries > 0:
                print(f"Retrying upload of {file} in 5 seconds...")
                time.sleep(5)
        
        if retries == 0:
            print(f"Failed to upload {file} after 3 attempts")


def get_room_status(room_id):
    response = requests.get(f"{BASE_URL}/room_status", params={"room_id": room_id})
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get room status. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def render_loop(room_id, client_id):
    print("尝试开始渲染...")
    
    # 检查房间状态
    status = get_room_status(room_id)
    if status is None:
        print("获取房间状态失败。退出渲染循环。")
        return

    if status['status'] != 'triggered' and status['status'] != 'rendering':
        print(f"房间尚未准备好进行渲染。当前状态：{status['status']}")
        
        # 获取房间设置以确定房主
        room_settings = get_room_settings(room_id)
        if room_settings and room_settings['members']:
            owner_id = room_settings['members'][0]['id']  # 第一个成员（序号为0）是房主
            print(f"请等待房主（client_id: {owner_id}）触发房间。")
        else:
            print("无法确定房主。请等待房间被触发。")
        return

    # 尝试下载 tasks.json
    tasks_file_path = f"./render/{room_id}/log/tasks.json"
    if not download_file(f"{BASE_URL}/download_tasks?room_id={room_id}", tasks_file_path):
        print("下载 tasks.json 失败。房间可能尚未被触发。")
        return

    try:
        with open(tasks_file_path, 'r') as f:
            tasks = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"读取 tasks.json 时出错：{e}")
        return

    available_tasks = [task for task in tasks if task['status'] == 'triggered' and task['client'] == client_id]
    
    if not available_tasks:
        print("该客户端没有可用的任务。")
        return

    for task in available_tasks:
        print(f"处理任务：{task['id']}")
        update_task_status(room_id, task['id'], 'rendering', client_id)
        print(f"房间状态已经更改为渲染中")
        
        # 检查任务是否包含所需的所有键
        required_keys = ['id', 'file_name', 'start_frame', 'end_frame']
        if not all(key in task for key in required_keys):
            print(f"任务 {task['id']} 缺少必要的信息。跳过此任务。")
            print(f"任务详情：{task}")
            continue

        # 使用 'file_name' 而不是 'file'
        blend_file = os.path.join("render", room_id, "queue", task['file_name'])
        output_dir = os.path.join("render", room_id, "results", task['id'])
        os.makedirs(output_dir, exist_ok=True)

        start_frame = task['start_frame']
        end_frame = task['end_frame']

        print(f"开始渲染 {blend_file}，帧范围：{start_frame}-{end_frame}")
        result = render_blender(blend_file, output_dir, start_frame, end_frame)

        if isinstance(result, int) and result == end_frame:
            print(f"任务 {task['id']} 渲染成功完成")
            update_task_status(room_id, task['id'], 'done', client_id)
            
            # 准备上传文件
            final_dir = os.path.join("render", room_id, "final")
            # 创建final目录
            os.makedirs(final_dir, exist_ok=True)
            # 将渲染结果移动到final目录
            move_results_to_final(room_id, task['id'])
            
            # 准备上传文件  
            files_to_upload = [os.path.join(final_dir, f) for f in os.listdir(final_dir) if os.path.isfile(os.path.join(final_dir, f))]
            
            # 使用upload_batch端点上传文件
            files = [('files', (os.path.basename(f), open(f, 'rb'))) for f in files_to_upload]
            data = {'room_id': room_id,"task_id":task['id']}
            response = requests.post(f"{BASE_URL}/upload_batch", files=files, data=data)
            
            if response.status_code == 200:
                print(f"成功上传任务 {task['id']} 的渲染结果")
            else:
                print(f"上传任务 {task['id']} 的渲染结果失败：{response.text}")

            
            # 尝试下载 tasks.json
            tasks_file_path = f"./render/{room_id}/log/tasks.json"
            if not download_file(f"{BASE_URL}/download_tasks?room_id={room_id}", tasks_file_path):
                print("下载 tasks.json 失败。房间可能尚未被触发。")
            
        else:
            print(f"任务 {task['id']} 渲染失败")
            update_task_status(room_id, task['id'], 'failed', client_id)
            # 尝试下载 tasks.json
            tasks_file_path = f"./render/{room_id}/log/tasks.json"
            if not download_file(f"{BASE_URL}/download_tasks?room_id={room_id}", tasks_file_path):
                print("下载 tasks.json 失败。房间可能尚未被触发。")

    print("所有任务已完成。")


def update_task_status(room_id, task_id, status, client_id):
    response = requests.post(f"{BASE_URL}/update_task", json={
        "room_id": room_id,
        "task_id": task_id,
        "status": status,
        "client_id": client_id
    })
    if response.status_code != 200:
        print(f"Failed to update task status: {response.text}")
    return response.status_code

def move_results_to_final(room_id, task_id):
    source_dir = os.path.join("render", room_id, "results", task_id)
    target_dir = os.path.join("render", room_id, "final")
    os.makedirs(target_dir, exist_ok=True)
    for file in os.listdir(source_dir):
        shutil.move(os.path.join(source_dir, file), os.path.join(target_dir, file))

def upload_results(room_id, task_id):
    final_dir = os.path.join("render", room_id, "final")
    for file in os.listdir(final_dir):
        file_path = os.path.join(final_dir, file)
        upload_file(file_path, f"{BASE_URL}/upload_result", data={"room_id": room_id, "task_id": task_id})

def move_render_results(room_id, task):
    source_dir = os.path.join("render", room_id, "results", task['id'])
    target_dir = os.path.join("render", room_id, "render", os.path.splitext(os.path.basename(task['file']))[0])
    os.makedirs(target_dir, exist_ok=True)
    
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        target_file = os.path.join(target_dir, filename)
        shutil.move(source_file, target_file)
    
    print(f"Moved render results from {source_dir} to {target_dir}")

def load_room(room_id):
    response = requests.get(f"{BASE_URL}/room_status", params={"room_id": room_id})
    if response.status_code == 200:
        room_status = response.json()
        print(f"Room {room_id} loaded successfully")
        print(f"Room status: {room_status}")
        return room_id
    else:
        print(f"Failed to load room {room_id}")
        return None

def download_render_results(room_id):
    logging.info(f"Downloading render results for room {room_id}")
    
    # 获取服务器上 final 文件夹中的文件列表
    response = requests.get(f"{BASE_URL}/list_final_files", params={"room_id": room_id})
    if response.status_code != 200:
        logging.error("Failed to get final files list from server")
        return
    
    server_files = response.json()["files"]
    
    # 检查本地 final 文件夹中的文件
    local_final_dir = os.path.join("render", room_id, "final")
    os.makedirs(local_final_dir, exist_ok=True)
    local_files = set(os.listdir(local_final_dir))
    
    # 确需要下载的文件
    files_to_download = [f for f in server_files if f not in local_files]
    
    # 下载缺失的文件
    for file in files_to_download:
        url = f"{BASE_URL}/download_final_file?room_id={room_id}&file_name={file}"
        local_path = os.path.join(local_final_dir, file)
        if download_file(url, local_path):
            logging.info(f"Downloaded {file}")
        else:
            logging.error(f"Failed to download {file}")
    
    # 检查任务状态
    response = requests.get(f"{BASE_URL}/get_tasks", params={"room_id": room_id})
    if response.status_code != 200:
        logging.error("Failed to get tasks from server")
        return
    
    tasks = response.json()["tasks"]
    
    # 检查任务状态
    all_done = all(task["status"] == "done" for task in tasks)
    missing_tasks = [task for task in tasks if task["status"] != "done"]
    
    result = {
        "result": "done" if all_done else "incomplete",
        "missing": {task["id"]: task["status"] for task in missing_tasks}
    }
    
    print("Download result:", result)
    return result

def handle_room_actions(room_id, client_id):
    while True:
        print("\n1. Upload Blender file")
        print("2. Trigger rendering")
        print("3. Start rendering")
        print("4. Download render results")
        print("5. Check room status")  # 新增选项
        print("6. Exit")
        action = input("Enter your choice (1, 2, 3, 4, 5, or 6): ")
        if action == "1":
            blend_file_path = input("Enter the path to the Blender file: ")
            upload_blend_file(room_id, blend_file_path)
        elif action == "2":
            if trigger_rendering(room_id):
                print("Room triggered successfully. You can now start rendering.")
            else:
                print("Failed to trigger room.")
        elif action == "3":
            render_loop(room_id, client_id)
        elif action == "4":
            download_render_results(room_id)
        elif action == "5":
            status = get_room_status(room_id)
            if status:
                print(f"Current room status: {status['status']}")
            else:
                print("Failed to get room status.")
        elif action == "6":
            break
        else:
            print("Invalid choice. Please try again.")

def main():
    print("1. Create a room")
    print("2. Join a room")
    print("3. Load a room")
    choice = input("Enter your choice (1, 2, or 3): ")

    if choice == "1":
        room_id, client_id = create_room()
        if room_id and client_id:
            setup_logging(room_id)
            handle_room_actions(room_id, client_id)
    elif choice == "2":
        target_room_id = input("请输入房间ID:")
        room_id, client_id, response = join_room(target_room_id)
        if room_id and client_id:
            setup_logging(room_id)
            handle_room_actions(room_id, client_id)  # 改为 handle_room_actions
    elif choice == "3":
        room_id = load_room()
        if room_id:
            setup_logging(room_id)
            client_id = f"loader_{int(time.time())}"
            requests.post(f"{BASE_URL}/join_room", json={"room_id": room_id, "client_id": client_id})
            handle_room_actions(room_id, client_id)
    else:
        print("Invalid choice")

def get_client_id():
    config_path = 'user_config.json'
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        client_id = config.get('client_id')
        if client_id:
            return client_id
    
    # 如果没有找到 client_id，生成一个新的
    client_id = f"client_{int(time.time())}"
    with open(config_path, 'w') as f:
        json.dump({'client_id': client_id}, f)
    return client_id

def download_room_settings(room_id):
    url = f"{BASE_URL}/download_room_settings?room_id={room_id}"
    local_path = f"./render/{room_id}/log/room_settings.json"
    success = download_file(url, local_path)
    if success:
        print(f"Successfully downloaded room_settings.json to {local_path}")
    else:
        print(f"Failed to download room_settings.json")

def upload_file(file_path, url, data=None):
    try:
        with open(file_path, 'rb') as file:
            files = {'file': (os.path.basename(file_path), file)}
            response = requests.post(url, files=files, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return False

if __name__ == "__main__":
    main()