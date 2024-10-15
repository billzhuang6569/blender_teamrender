# WOE Blender Teamrender

## 项目简介

WOE Blender Teamrender是一个分布式渲染系统,允许多个客户端协同工作,共同完成Blender项目的渲染任务。该系统包括服务器端和客户端组件,支持任务分配、文件传输等功能。

## 主要特性

- 多客户端协作渲染
- 自动任务分配和负载均衡
- 实时渲染进度跟踪
- 支持多个Blender项目同时渲染
- 文件上传下载和结果管理
- 用户友好的Web界面

## 系统架构

项目分为服务器端和客户端两个主要部分:

### 服务器端

- `server/api_server.py`: Flask-based API服务器,处理客户端请求
- `utils/room_manager.py`: 管理渲染房间和任务分配
- `config.py`: 服务器配置文件

### 客户端

- `client.py`: 客户端核心逻辑,负责与服务器通信和本地渲染
- `web.py`: 基于Gradio的Web界面
- `utils/`: 包含各种辅助功能的模块


## Quick Start
- Windows用户：运行StartonWin.exe
- Mac用户：运行StartonMac.app


## Server安装指南

1. 克隆仓库:   ```
   git clone https://github.com/your-repo/blender_teamrender.git
   cd blender_teamrender   ```

2. 安装依赖:   ```
   pip install -r requirements.txt   ```

3. 配置服务器:
   - 编辑 `user_config.json` 文件,设置服务器IP和端口
   - 确保 `UPLOAD_FOLDER` 和 `ROOMS_FOLDER` 路径正确

4. 启动服务器:   ```
   python api_server.py   ```   