import os
import json
import shutil
import logging
from datetime import datetime
from config import ROOMS_FOLDER, IS_SERVER
from utils.get_render_settings import get_render_settings

class RoomManager:
    def __init__(self):
        self.rooms = {}

    def create_room(self, room_id, room_settings):
        if room_id in self.rooms:
            raise ValueError("Room already exists")
        
        # 创建房间目录结构
        room_path = os.path.join(ROOMS_FOLDER, room_id)
        os.makedirs(os.path.join(room_path, "queue"), exist_ok=True)
        os.makedirs(os.path.join(room_path, "log"), exist_ok=True)
        os.makedirs(os.path.join(room_path, "results"), exist_ok=True)
        
        self.rooms[room_id] = room_settings
        self._save_room_settings(room_id, room_settings)

    def join_room(self, room_id, client_id):
        room_settings = self.get_room_settings(room_id)
        if room_settings['status'] != 'waiting':
            raise ValueError("Room is not in waiting status")
        max_order = max([member['order'] for member in room_settings['members']])
        room_settings['members'].append({"id": client_id, "order": max_order + 1})
        self.update_room_settings(room_id, room_settings)

    def get_room_settings(self, room_id):
        room_settings_path = os.path.join(ROOMS_FOLDER, room_id, "log", "room_settings.json")
        if not os.path.exists(room_settings_path):
            raise ValueError(f"Room settings file not found for room {room_id}")
        with open(room_settings_path, 'r') as f:
            return json.load(f)

    def update_room_settings(self, room_id, room_settings):
        if room_id not in self.rooms:
            raise ValueError("Room not found")
        self.rooms[room_id] = room_settings
        self._save_room_settings(room_id, room_settings)

    def trigger_rendering(self, room_id):
        room_settings = self.get_room_settings(room_id)
        if room_settings['status'] != 'waiting':
            raise ValueError("Room is not in waiting status")
        
        room_settings['status'] = 'triggered'
        self.update_room_settings(room_id, room_settings)
        
        # 创建任务
        self._create_tasks(room_id)

    def get_tasks(self, room_id):
        tasks_file_path = os.path.join(ROOMS_FOLDER, room_id, "log", "tasks.json")
        if not os.path.exists(tasks_file_path):
            return []
        with open(tasks_file_path, 'r') as f:
            return json.load(f)
    def update_task(self, room_id, task_id, status, client_id):
        tasks = self.get_tasks(room_id)
        for task in tasks:
            if task['id'] == task_id:
                task['status'] = status
                task['client'] = client_id
                break
        else:
            raise ValueError("Task not found")
        
        tasks_file_path = os.path.join(ROOMS_FOLDER, room_id, "log", "tasks.json")
        with open(tasks_file_path, 'w') as f:
            json.dump(tasks, f, indent=2)

    def _create_tasks(self, room_id):
        room_settings = self.get_room_settings(room_id)
        tasks = []
        client_count = len(room_settings['members'])
        client_index = 0
        
        for blender_file in room_settings["blender_files"]:
            file_name = blender_file["file_name"]
            render_settings = blender_file["render_settings"]
            start_frame = render_settings["start_frame"]
            end_frame = render_settings["end_frame"]
            
            frames_per_task = 10
            for i in range(start_frame, end_frame + 1, frames_per_task):
                task_end_frame = min(i + frames_per_task - 1, end_frame)
                task = {
                    "id": f"{room_id}_{file_name}_{i}",
                    "file_name": file_name,
                    "start_frame": i,
                    "end_frame": task_end_frame,
                    "status": "triggered",
                    "client": room_settings['members'][client_index]['id']
                }
                tasks.append(task)
                client_index = (client_index + 1) % client_count
        
        tasks_file_path = os.path.join(ROOMS_FOLDER, room_id, "log", "tasks.json")
        with open(tasks_file_path, 'w') as f:
            json.dump(tasks, f, indent=2)

    def _save_room_settings(self, room_id, room_settings):
        room_settings_path = os.path.join(ROOMS_FOLDER, room_id, "log", "room_settings.json")
        os.makedirs(os.path.dirname(room_settings_path), exist_ok=True)  # 确保目录存在
        with open(room_settings_path, 'w') as f:
            json.dump(room_settings, f, indent=2)

    def get_room_status(self, room_id):
        room_settings = self.get_room_settings(room_id)
        return {
            "status": room_settings['status'],
            "members": len(room_settings['members']),
            "blender_files": len(room_settings['blender_files'])
        }

    def start_rendering(self, room_id):
        room_settings = self.get_room_settings(room_id)
        if room_settings['status'] != 'triggered':
            raise ValueError(f"Room is not in triggered status. Current status: {room_settings['status']}")
        room_settings['status'] = 'rendering'
        self.update_room_settings(room_id, room_settings)
        logging.info(f"Room {room_id} status updated to 'rendering'")
