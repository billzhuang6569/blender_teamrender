import sys
import os
import unittest
import logging

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.get_render_settings import get_render_settings

class TestGetRenderSettings(unittest.TestCase):
    def setUp(self):
        # 设置测试用的 Blender 文件路径
        self.test_blend_file = "/Users/billzhuang/Desktop/test_render.blend"
        self.test_room_id = "test_room"
        
        # 设置日志
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    def test_get_render_settings(self):
        try:
            settings = get_render_settings(self.test_blend_file, self.test_room_id)
            
            # 检查是否成功获取到设置
            self.assertIsNotNone(settings)
            self.assertIsInstance(settings, dict)

            # 检查是否包含所有预期的键
            expected_keys = ["renderer", "start_frame", "end_frame", "resolution_x", "resolution_y", "resolution_percentage", "file_format"]
            for key in expected_keys:
                self.assertIn(key, settings)

            # 打印获取到的设置，以便手动检查
            print("Render settings:")
            for key, value in settings.items():
                print(f"{key}: {value}")

            # 可以添加更多具体的断言来验证设置的值
            self.assertGreater(settings["resolution_x"], 0)
            self.assertGreater(settings["resolution_y"], 0)
            self.assertGreaterEqual(settings["start_frame"], 1)
            self.assertGreaterEqual(settings["end_frame"], settings["start_frame"])

        except Exception as e:
            logging.exception("An error occurred during the test")
            self.fail(f"get_render_settings raised an exception: {str(e)}")

if __name__ == '__main__':
    unittest.main()