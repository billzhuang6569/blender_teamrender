import sys
import os
import requests
from requests.exceptions import RequestException
import json

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import server_ip, server_port

# 使用您的 VPS 地址和端口
BASE_URL = f"http://{server_ip}:{server_port}"

def print_response(response):
    print(f"Status Code: {response.status_code}")
    print("Response:")
    try:
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.JSONDecodeError:
        print(response.text)
    print()

def test_room_and_render():
    try:
        # 创建房间
        room_id = "123456"
        response = requests.post(f"{BASE_URL}/create_room", json={"room_id": room_id}, timeout=10)
        response.raise_for_status()
        print("创建房间:")
        print_response(response)
    except RequestException as e:
        print(f"请求失败: {e}")
        print(f"请求 URL: {e.request.url}")
        print(f"请求方法: {e.request.method}")
        print(f"请求头: {e.request.headers}")
        print(f"请求体: {e.request.body}")
        if e.response is not None:
            print(f"响应状态码: {e.response.status_code}")
            print(f"响应头: {e.response.headers}")
            print(f"响应内容: {e.response.text}")
        return

    # 加入房间
    client_id = "test_client"
    response = requests.post(f"{BASE_URL}/join_room", json={"room_id": room_id, "client_id": client_id})
    print("加入房间:")
    print_response(response)

    # 上传 Blender 文件
    local_blend_file = "/Users/billzhuang/Desktop/test_render.blend"  # 替换为您本地的 Blender 文件路径
    with open(local_blend_file, 'rb') as file:
        response = requests.post(f"{BASE_URL}/upload", files={"file": file})
    print("上传 Blender 文件:")
    print_response(response)

    # 添加上传的 Blender 文件到房间
    blend_file_name = os.path.basename(local_blend_file)
    response = requests.post(f"{BASE_URL}/add_blend_file", json={"room_id": room_id, "file_path": f"/usr/teamrender/upload/{blend_file_name}"})
    print("添加 Blender 文件到房间:")
    print_response(response)

    # 获取下一个任务
    response = requests.get(f"{BASE_URL}/get_next_task?room_id={room_id}&client_id={client_id}")
    print("获取下一个任务:")
    print_response(response)

    # 完成任务
    if response.json()["success"] and response.json()["task"]:
        task_id = response.json()["task"]["id"]
        response = requests.post(f"{BASE_URL}/complete_task", json={"room_id": room_id, "task_id": task_id})
        print("完成任务:")
        print_response(response)

    # 离开房间
    response = requests.post(f"{BASE_URL}/leave_room", json={"room_id": room_id, "client_id": client_id})
    print("离开房间:")
    print_response(response)

if __name__ == "__main__":
    test_room_and_render()