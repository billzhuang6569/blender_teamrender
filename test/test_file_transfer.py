import asyncio
import os
import sys
import unittest
from unittest.mock import patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.file_transfer import upload_batch, download_batch

class TestFileTransfer(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.server_url = 'http://154.40.35.34:5801'  # 更新端口为5801
        self.test_files_dir = os.path.join(os.path.dirname(__file__), 'test_files')
        self.output_dir = os.path.join(os.path.dirname(__file__), 'output')
        
        # 创建测试文件夹和输出文件夹
        os.makedirs(self.test_files_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 创建测试文件
        for i in range(3):
            with open(os.path.join(self.test_files_dir, f'test_file_{i}.txt'), 'w') as f:
                f.write(f'This is test file {i}')

    async def test_upload_and_download_batch(self):
        # 准备上传文件列表
        upload_files = [os.path.join(self.test_files_dir, f) for f in os.listdir(self.test_files_dir)]
        
        # 测试上传
        upload_result = await upload_batch(f'{self.server_url}/upload_batch', upload_files)
        self.assertIn('message', upload_result)
        self.assertEqual(upload_result['message'], 'Files uploaded successfully')
        self.assertEqual(len(upload_result['files']), len(upload_files))
        
        # 测试下载
        download_files = [os.path.basename(f) for f in upload_files]
        await download_batch(f'{self.server_url}/download_batch', download_files, self.output_dir)
        
        # 验证下载的文件
        for file in download_files:
            self.assertTrue(os.path.exists(os.path.join(self.output_dir, file)))
            with open(os.path.join(self.output_dir, file), 'r') as f:
                content = f.read()
                self.assertIn('This is test file', content)

    def tearDown(self):
        # 清理测试文件和输出文件
        for file in os.listdir(self.test_files_dir):
            os.remove(os.path.join(self.test_files_dir, file))
        for file in os.listdir(self.output_dir):
            os.remove(os.path.join(self.output_dir, file))
        os.rmdir(self.test_files_dir)
        os.rmdir(self.output_dir)

if __name__ == '__main__':
    unittest.main()