import unittest
import sys
import os
import random
import string
import shutil
import tempfile

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.room_manager import RoomManager
import utils.get_render_settings as render_settings_module

class TestRenderProcess(unittest.TestCase):
    def setUp(self):
        self.test_render_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "render")
        if not os.path.exists(self.test_render_dir):
            os.makedirs(self.test_render_dir)
        
        self.room_manager = RoomManager()
        self.room_id = ''.join(random.choices(string.digits, k=6))
        self.blend_file = "test_render.blend"
        self.mock_settings = {
            "start_frame": 1,
            "end_frame": 50,
            "frame_rate": 24,
            "resolution_x": 1920,
            "resolution_y": 1080,
            "file_format": "PNG",
            "output_path": "/tmp/"
        }
        self.temp_dir = tempfile.mkdtemp()

    def create_mock_blend_file(self):
        blend_file_path = os.path.join(self.temp_dir, self.blend_file)
        with open(blend_file_path, 'w') as f:
            f.write("Mock Blender file content")
        return blend_file_path

    def test_render_process(self):
        # 创建房间
        self.room_manager.create_room(self.room_id)

        # 模拟添加 Blender 文件
        blend_file_path = self.create_mock_blend_file()

        # 模拟获取渲染设置
        original_get_render_settings = render_settings_module.get_render_settings
        render_settings_module.get_render_settings = lambda file_path: self.mock_settings

        try:
            # 添加 Blender 文件到房间
            self.room_manager.add_blend_file(self.room_id, blend_file_path)

            # 触发渲染
            self.room_manager.trigger_rendering(self.room_id)

            # 开始渲染
            self.room_manager.start_rendering(self.room_id)

            # 验证任务分配
            tasks = self.room_manager.rooms[self.room_id]["tasks"]
            self.assertEqual(len(tasks), 5)  # 50帧应该被分成5个任务

            expected_frames = [(1, 10), (11, 20), (21, 30), (31, 40), (41, 50)]
            for task, (start, end) in zip(tasks, expected_frames):
                self.assertEqual(task["start_frame"], start)
                self.assertEqual(task["end_frame"], end)
                self.assertEqual(task["status"], "pending")

            # 模拟多个用户获取和完成任务
            client_ids = [f"client_{i}" for i in range(3)]
            for i, client_id in enumerate(client_ids):
                task = self.room_manager.get_next_task(self.room_id, client_id)
                self.assertIsNotNone(task)
                self.assertEqual(task["status"], "in_progress")
                self.assertEqual(task["client"], client_id)

                # 完成任务
                self.room_manager.complete_task(self.room_id, task["id"])

            # 验证任务状态
            completed_tasks = [task for task in tasks if task["status"] == "completed"]
            in_progress_tasks = [task for task in tasks if task["status"] == "in_progress"]
            pending_tasks = [task for task in tasks if task["status"] == "pending"]

            self.assertEqual(len(completed_tasks), 3)
            self.assertEqual(len(in_progress_tasks), 0)
            self.assertEqual(len(pending_tasks), 2)

        finally:
            # 恢复原始的 get_render_settings 函数
            render_settings_module.get_render_settings = original_get_render_settings

    def tearDown(self):
        # 清理测试目录
        if os.path.exists(os.path.join(self.test_render_dir, self.room_id)):
            shutil.rmtree(os.path.join(self.test_render_dir, self.room_id))
        # 清理临时目录
        shutil.rmtree(self.temp_dir)

if __name__ == '__main__':
    unittest.main()