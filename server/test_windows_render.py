import unittest
import os
import sys
import tempfile
import shutil
import requests
import platform

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.render import render_blender
from config import BLENDER_PATH, IS_SERVER
from utils.file_transfer import download_file
from client import download_blend_file

class TestWindowsRender(unittest.TestCase):

    def setUp(self):
        self.test_room_id = "333333"  # 使用已知存在的房间 ID
        self.test_file_name = "test_render.blend"
        self.test_output_dir = tempfile.mkdtemp()
        self.base_url = "http://154.40.35.34:5801"  # 确保这是正确的服务器地址

    def tearDown(self):
        shutil.rmtree(self.test_output_dir)

    def test_download_blend_file(self):
        # 使用已知存在的文件路径
        server_file_path = f"/usr/teamrender/rooms/{self.test_room_id}/queue/{self.test_file_name}"
        url = f"{self.base_url}/download_blend_file?room_id={self.test_room_id}&file_path={server_file_path}"
        local_path = os.path.join(self.test_output_dir, self.test_file_name)
        
        # 测试直接使用 requests 下载
        response = requests.get(url)
        print(f"Download URL: {url}")
        print(f"Response status code: {response.status_code}")
        print(f"Response content type: {response.headers.get('Content-Type')}")
        print(f"Response content length: {len(response.content)} bytes")
        
        self.assertEqual(response.status_code, 200, f"下载失败，状态码：{response.status_code}")
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        self.assertTrue(os.path.exists(local_path), "文件未成功下载")
        self.assertGreater(os.path.getsize(local_path), 0, "下载的文件是空的")

        # 测试使用 download_file 函数
        os.remove(local_path)
        success = download_file(url, local_path)
        self.assertTrue(success, "download_file 函数下载失败")
        self.assertTrue(os.path.exists(local_path), "文件未成功下载")
        self.assertGreater(os.path.getsize(local_path), 0, "下载的文件是空的")

        # 测试使用 client.py 中的 download_blend_file 函数
        os.remove(local_path)
        success = download_blend_file(self.test_room_id, server_file_path)
        self.assertTrue(success, "download_blend_file 函数下载失败")
        downloaded_file = os.path.join("render", self.test_room_id, "queue", self.test_file_name)
        self.assertTrue(os.path.exists(downloaded_file), "文件未成功下载")
        self.assertGreater(os.path.getsize(downloaded_file), 0, "下载的文件是空的")

    @unittest.skipIf(IS_SERVER, "在服务器环境中跳过渲染测试")
    def test_render_blender(self):
        # 首先下载 Blender 文件
        self.test_download_blend_file()
        blend_file = os.path.join("render", self.test_room_id, "queue", self.test_file_name)
        
        start_frame = 1
        end_frame = 5

        result = render_blender(blend_file, self.test_output_dir, start_frame, end_frame)

        self.assertIsInstance(result, int, "渲染结果应该是一个整数")
        self.assertEqual(result, end_frame, "渲染未能完成所有帧")

        for frame in range(start_frame, end_frame + 1):
            output_file = os.path.join(self.test_output_dir, f"frame_{frame:04d}.png")
            self.assertTrue(os.path.exists(output_file), f"未找到渲染输出文件：{output_file}")

        print(f"Blender 渲染测试完成，输出目录：{self.test_output_dir}")

    def test_room_status(self):
        url = f"{self.base_url}/room_status?room_id={self.test_room_id}"
        response = requests.get(url)
        print(f"Room status URL: {url}")
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        self.assertEqual(response.status_code, 200, "获取房间状态失败")

if __name__ == '__main__':
    unittest.main()