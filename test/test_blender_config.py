import unittest
import os
import sys
import platform

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.blender_config import get_blender_paths
from config import BLENDER_PATH, IS_SERVER

class TestBlenderConfig(unittest.TestCase):

    def test_get_blender_paths(self):
        if not IS_SERVER:
            blender_executable, blender_python_path = get_blender_paths()

            # 测试 Blender 可执行文件路径
            self.assertIsNotNone(blender_executable)
            self.assertTrue(os.path.exists(blender_executable))
            self.assertTrue(os.path.isfile(blender_executable))

            # 测试 Blender Python 路径
            self.assertIsNotNone(blender_python_path)
            self.assertTrue(os.path.exists(blender_python_path))
            self.assertTrue(os.path.isdir(blender_python_path))

            # 验证 Blender 可执行文件路径是否正确
            if platform.system() == "Darwin":
                self.assertEqual(blender_executable, "/Applications/Blender.app/Contents/MacOS/Blender")
            else:
                self.assertTrue(blender_executable.startswith(BLENDER_PATH))

            print(f"Blender 可执行文件路径: {blender_executable}")
            print(f"Blender Python 路径: {blender_python_path}")
        else:
            print("在服务器环境中跳过 Blender 路径测试")

if __name__ == '__main__':
    unittest.main()