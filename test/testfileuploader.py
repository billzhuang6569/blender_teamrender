import unittest
import os
import sys
import tempfile
import paramiko
from unittest.mock import patch, MagicMock

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.dirname(current_dir)
# 将项目根目录添加到Python路径
sys.path.insert(0, project_root)
from app.file_uploader import upload_file

class TestFileUploader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, 'test_file.txt')
        with open(self.test_file_path, 'w') as f:
            f.write('This is a test file')

    def tearDown(self):
        os.remove(self.test_file_path)
        os.rmdir(self.temp_dir)

    @patch('paramiko.SSHClient')
    def test_upload_file_success(self, mock_ssh):
        # 模拟SSH连接和SFTP客户端
        mock_sftp = MagicMock()
        mock_ssh.return_value.open_sftp.return_value = mock_sftp

        # 调用上传函数
        upload_file('test_host', 22, 'test_user', 'test_pass', self.test_file_path, '/remote/path')

        # 验证SSH连接是否正确建立
        mock_ssh.return_value.connect.assert_called_once_with('test_host', port=22, username='test_user', password='test_pass')

        # 验证文件是否正确上传
        mock_sftp.put.assert_called_once_with(self.test_file_path, '/remote/path/test_file.txt')

        # 验证连接是否正确关闭
        mock_sftp.close.assert_called_once()
        mock_ssh.return_value.close.assert_called_once()

    @patch('paramiko.SSHClient')
    def test_upload_file_failure(self, mock_ssh):
        # 模拟SSH连接失败
        mock_ssh.return_value.connect.side_effect = paramiko.SSHException("Connection failed")

        # 调用上传函数并捕获输出
        with patch('builtins.print') as mock_print:
            upload_file('test_host', 22, 'test_user', 'test_pass', self.test_file_path, '/remote/path')

        # 验证是否打印了正确的错误消息
        mock_print.assert_called_with("上传文件时发生错误：Connection failed")

if __name__ == '__main__':
    unittest.main()
