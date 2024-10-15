import unittest
import os
import sys
import tempfile
import shutil

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.file_transfer import download_file
from config import server_ip, server_port, ROOMS_FOLDER

class TestDownloadBlenderFile(unittest.TestCase):

    def setUp(self):
        self.test_room_id = "333333"
        self.test_file_name = "test_render.blend"
        self.base_url = f"http://{server_ip}:{server_port}"
        self.test_output_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_output_dir)

    def test_download_blender_file(self):
        # 构造下载 URL
        server_file_path = f"{ROOMS_FOLDER}/{self.test_room_id}/queue/{self.test_file_name}"
        url = f"{self.base_url}/download_blend_file?room_id={self.test_room_id}&file_path={server_file_path}"
        
        # 设置本地保存路径
        local_path = os.path.join(self.test_output_dir, self.test_file_name)

        # 下载文件
        success = download_file(url, local_path)

        # 验证下载是否成���
        self.assertTrue(success, "文件下载失败")
        self.assertTrue(os.path.exists(local_path), "下载的文件不存在")
        self.assertGreater(os.path.getsize(local_path), 0, "下载的文件是空的")

        print(f"文件成功下载到: {local_path}")
        print(f"文件大小: {os.path.getsize(local_path)} 字节")

if __name__ == '__main__':
    unittest.main()