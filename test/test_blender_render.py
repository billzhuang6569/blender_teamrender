import unittest
import os
import sys
import tempfile
import shutil

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.render import render_blender
from config import BLENDER_PATH, IS_SERVER

class TestBlenderRender(unittest.TestCase):

    def setUp(self):
        # 创建一个临时目录用于测试输出
        self.test_output_dir = tempfile.mkdtemp()

    def tearDown(self):
        # 清理临时目录
        shutil.rmtree(self.test_output_dir)

    def test_render_blender(self):
        if IS_SERVER:
            print("在服务器环境中跳过 Blender 渲染测试")
            return

        # 使用一个简单的 Blender 文件进行测试
        # 注意：你需要提供一个有效的 .blend 文件路径
        test_blend_file = "/path/to/your/test.blend"
        
        if not os.path.exists(test_blend_file):
            self.skipTest("测试用的 .blend 文件不存在")

        start_frame = 1
        end_frame = 5

        result = render_blender(test_blend_file, self.test_output_dir, start_frame, end_frame)

        # 检查渲染是否成功完成
        self.assertEqual(result, end_frame, "渲染未能完成所有帧")

        # 检查输出文件是否存在
        for frame in range(start_frame, end_frame + 1):
            output_file = os.path.join(self.test_output_dir, f"frame_{frame:04d}.png")
            self.assertTrue(os.path.exists(output_file), f"未找到渲染输出文件：{output_file}")

        print(f"Blender 渲染测试完成，输出目录：{self.test_output_dir}")

if __name__ == '__main__':
    unittest.main()