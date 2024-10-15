import asyncio
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.room_manager import RoomManager

class TestRoomManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.room_manager = RoomManager('https://154.40.35.34:5801')

    @patch('aiohttp.ClientSession.post')
    async def test_create_room(self, mock_post):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = {'room_id': '123456'}
        mock_post.return_value.__aenter__.return_value = mock_response

        room_id = await self.room_manager.create_room()
        self.assertEqual(room_id, '123456')

    @patch('aiohttp.ClientSession.post')
    async def test_join_room_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_response

        success = await self.room_manager.join_room('123456')
        self.assertTrue(success)

    @patch('aiohttp.ClientSession.post')
    async def test_join_room_not_found(self, mock_post):
        mock_response = MagicMock()
        mock_response.status = 404
        mock_post.return_value.__aenter__.return_value = mock_response

        with self.assertRaises(Exception) as context:
            await self.room_manager.join_room('123456')
        self.assertTrue('Room not found' in str(context.exception))

if __name__ == '__main__':
    unittest.main()