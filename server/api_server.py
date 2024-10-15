# 运行在VPS上的API服务器
# 在config中设置UPLOAD_FOLDER
# 在config中设置ROOMS_FOLDER

import sys
import os
import shutil

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, send_file, jsonify
from utils.room_manager import RoomManager
import random
import string
import io
import zipfile
import os
import logging
import json
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
room_manager = RoomManager()

# 调用config.py中的UPLOAD_FOLDER和ROOMS_FOLDER
from config import UPLOAD_FOLDER, ROOMS_FOLDER

def generate_room_id():
    return ''.join(random.choices(string.digits, k=6))

logging.basicConfig(level=logging.DEBUG)

@app.route('/create_room', methods=['POST'])
def create_room():
    room_id = request.json['room_id']
    client_id = request.json['client_id']
    try:
        room_settings = {
            "room_id": room_id,
            "create_time": datetime.now().isoformat(),
            "status": "waiting",
            "members": [{"id": client_id, "order": 0}],  # 确保这行存在
            "blender_files": []
        }
        room_manager.create_room(room_id, room_settings)
        return jsonify({"success": True, "room_id": room_id})
    except ValueError as e:
        app.logger.error(f"Failed to create room: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Unexpected error while creating room: {str(e)}")
        return jsonify({"success": False, "error": "An unexpected error occurred"}), 500

@app.route('/join_room', methods=['POST'])
def join_room():
    room_id = request.json['room_id']
    client_id = request.json['client_id']
    try:
        room_settings = room_manager.get_room_settings(room_id)
        if room_settings['status'] != 'waiting':
            return jsonify({"success": False, "error": "Room is not in waiting status"}), 400
        room_manager.join_room(room_id, client_id)
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    

@app.route('/download_room_settings', methods=['GET'])
def download_room_settings():
    room_id = request.args.get('room_id')
    if not room_id:
        return jsonify({"error": "Missing room_id"}), 400
    
    room_settings_path = os.path.join(ROOMS_FOLDER, room_id, "log", "room_settings.json")
    if not os.path.exists(room_settings_path):
        return jsonify({"error": "Room settings file not found"}), 404
    
    with open(room_settings_path, 'r') as f:
        room_settings = json.load(f)
    
    return jsonify(room_settings)


@app.route('/download_tasks', methods=['GET'])
def download_tasks():
    room_id = request.args.get('room_id')
    if not room_id:
        return jsonify({"error": "Missing room_id"}), 400
    
    tasks_file_path = os.path.join(ROOMS_FOLDER, room_id, "log", "tasks.json")
    if not os.path.exists(tasks_file_path):
        return jsonify({"error": "Tasks file not found"}), 404
    
    return send_file(tasks_file_path, as_attachment=True)

@app.route('/leave_room', methods=['POST'])
def leave_room():
    room_id = request.json['room_id']
    client_id = request.json['client_id']
    room_manager.leave_room(room_id, client_id)
    return jsonify({"success": True})

@app.route('/add_blend_file', methods=['POST'])
def add_blend_file():
    room_id = request.json['room_id']
    file_path = request.json['file_path']
    try:
        room_settings = room_manager.get_room_settings(room_id)
        if room_settings['status'] != 'waiting':
            return jsonify({"success": False, "error": "Room is not in waiting status"}), 400
        
        render_settings_path = os.path.join(ROOMS_FOLDER, room_id, "log", "render_settings.json")
        with open(render_settings_path, 'r') as f:
            render_settings = json.load(f)
        
        file_name = os.path.basename(file_path)
        if file_name not in render_settings:
            return jsonify({"success": False, "error": f"Render settings for {file_name} not found"}), 400
        
        file_settings = render_settings[file_name]
        
        blender_file_info = {
            "file_name": file_name,
            "upload_order": len(room_settings["blender_files"]),
            "render_settings": file_settings
        }
        room_settings["blender_files"].append(blender_file_info)
        
        room_manager.update_room_settings(room_id, room_settings)
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Unexpected error in add_blend_file: {str(e)}")
        return jsonify({"success": False, "error": "An unexpected error occurred"}), 500

@app.route('/remove_blend_file', methods=['POST'])
def remove_blend_file():
    room_id = request.json['room_id']
    file_name = request.json['file_name']
    try:
        room_manager.remove_blend_file(room_id, file_name)
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/get_next_task', methods=['GET'])
def get_next_task():
    room_id = request.args.get('room_id')
    client_id = request.args.get('client_id')
    try:
        task = room_manager.get_next_task(room_id, client_id)
        return jsonify({"success": True, "task": task})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/complete_task', methods=['POST'])
def complete_task():
    room_id = request.json['room_id']
    task_id = request.json['task_id']
    try:
        room_manager.complete_task(room_id, task_id)
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    room_id = request.form.get('room_id')
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and room_id:
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(ROOMS_FOLDER, room_id, "queue" if filename.endswith('.blend') else "log")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        return jsonify({"message": "File uploaded successfully", "path": file_path}), 200
    return jsonify({"error": "Invalid request"}), 400

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

@app.route('/upload_batch', methods=['POST'])
def upload_batch():
    if 'files' not in request.files:
        return 'No file part', 400
    files = request.files.getlist('files')
    if not files:
        return 'No selected files', 400
    
    uploaded_files = []
    for file in files:
        if file.filename:
            filename = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filename)
            uploaded_files.append(file.filename)
    
    return jsonify({'message': 'Files uploaded successfully', 'files': uploaded_files}), 200

@app.route('/download_batch', methods=['POST'])
def download_batch():
    filenames = request.json.get('files', [])
    if not filenames:
        return 'No files specified', 400
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for filename in filenames:
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(file_path):
                zf.write(file_path, filename)
    
    memory_file.seek(0)
    return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name='batch_download.zip')

@app.route('/start_rendering', methods=['POST'])
def start_rendering():
    room_id = request.json['room_id']
    try:
        app.logger.info(f"Starting rendering for room {room_id}")
        room_settings = room_manager.get_room_settings(room_id)
        app.logger.info(f"Room settings before starting rendering: {room_settings}")
        room_manager.start_rendering(room_id)
        app.logger.info(f"Rendering started successfully for room {room_id}")
        return jsonify({"success": True, "message": "Rendering started"})
    except ValueError as e:
        app.logger.error(f"ValueError in start_rendering: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Unexpected error in start_rendering: {str(e)}")
        return jsonify({"success": False, "error": "An unexpected error occurred"}), 500

@app.route('/stop_rendering', methods=['POST'])
def stop_rendering():
    room_id = request.json['room_id']
    try:
        room_manager.stop_rendering(room_id)
        return jsonify({"success": True, "message": "Rendering stopped"})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/upload_result', methods=['POST'])
def upload_result():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    file = request.files['file']
    room_id = request.form['room_id']
    task_id = request.form['task_id']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
    if file:
        try:
            # 首先保存到 results 文件夹
            results_dir = os.path.join(ROOMS_FOLDER, room_id, "results", task_id)
            os.makedirs(results_dir, exist_ok=True)
            temp_filename = os.path.join(results_dir, file.filename)
            file.save(temp_filename)

            # 然后移动到 final 文件夹
            final_dir = os.path.join(ROOMS_FOLDER, room_id, "final")
            os.makedirs(final_dir, exist_ok=True)
            final_filename = os.path.join(final_dir, file.filename)
            shutil.move(temp_filename, final_filename)

            return jsonify({"success": True, "message": "Result file uploaded and moved to final folder successfully"}), 200
        except Exception as e:
            app.logger.error(f"Error processing uploaded file: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

@app.route('/update_render_log', methods=['POST'])
def update_render_log():
    room_id = request.json['room_id']
    frame_info = request.json['frame_info']
    try:
        room_manager.update_render_log(room_id, frame_info)
        return jsonify({"success": True})
    except Exception as e:
        app.logger.error(f"Error updating render log: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/get_render_log', methods=['GET'])
def get_render_log():
    room_id = request.args.get('room_id')
    try:
        render_log = room_manager.get_render_log(room_id)
        return jsonify(render_log)
    except Exception as e:
        app.logger.error(f"Error getting render log: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/trigger_rendering', methods=['POST'])
def trigger_rendering():
    room_id = request.json['room_id']
    try:
        room_settings = room_manager.get_room_settings(room_id)
        if room_settings['status'] != 'waiting':
            return jsonify({"success": False, "error": "Room is not in waiting status"}), 400
        
        room_manager.trigger_rendering(room_id)
        tasks = room_manager.get_tasks(room_id)
        return jsonify({"success": True, "message": "Rendering triggered", "tasks": tasks})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/update_task', methods=['POST'])
def update_task():
    room_id = request.json['room_id']
    task_id = request.json['task_id']
    status = request.json['status']
    client_id = request.json['client_id']
    try:
        room_manager.update_task(room_id, task_id, status, client_id)
        
        # 如果任务状态为 'done'，确保所有相关文件都被移动到 final 文件夹
        if status == 'done':
            results_dir = os.path.join(ROOMS_FOLDER, room_id, "results", task_id)
            final_dir = os.path.join(ROOMS_FOLDER, room_id, "final")
            os.makedirs(final_dir, exist_ok=True)
            
            for file in os.listdir(results_dir):
                src = os.path.join(results_dir, file)
                dst = os.path.join(final_dir, file)
                shutil.move(src, dst)
            
            # 可选：删除空的 results 子文件夹
            shutil.rmtree(results_dir)
        
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/room_status', methods=['GET'])
def room_status():
    room_id = request.args.get('room_id')
    try:
        status = room_manager.get_room_status(room_id)
        return jsonify(status)
    except ValueError as e:
        app.logger.error(f"Error getting room status: {str(e)}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        app.logger.error(f"Unexpected error getting room status: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/download_blend_file', methods=['GET'])
def download_blend_file():
    room_id = request.args.get('room_id')
    file_path = request.args.get('file_path')
    app.logger.info(f"Received download request: room_id={room_id}, file_path={file_path}")
    
    if not room_id or not file_path:
        app.logger.error("Missing room_id or file_path")
        return jsonify({"error": "Missing room_id or file_path"}), 400
    
    full_path = os.path.join(ROOMS_FOLDER, room_id, "queue", os.path.basename(file_path))
    app.logger.info(f"Full path: {full_path}")
    
    if not os.path.exists(full_path):
        app.logger.error(f"File not found: {full_path}")
        return jsonify({"error": "File not found"}), 404
    
    app.logger.info(f"Sending file: {full_path}")
    return send_file(full_path, as_attachment=True)

@app.route('/list_room_files', methods=['GET'])
def list_room_files():
    room_id = request.args.get('room_id')
    if not room_id:
        return jsonify({"error": "Missing room_id"}), 400
    
    room_path = os.path.join(ROOMS_FOLDER, room_id, "queue")
    if not os.path.exists(room_path):
        return jsonify({"error": "Room not found"}), 404
    
    files = os.listdir(room_path)
    return jsonify({"files": files})

@app.route('/download_render_results', methods=['GET'])
def download_render_results():
    room_id = request.args.get('room_id')
    if not room_id:
        return jsonify({"error": "Missing room_id"}), 400
    
    room_results_path = os.path.join(ROOMS_FOLDER, room_id, "results")
    if not os.path.exists(room_results_path):
        return jsonify({"error": "Room results not found"}), 404
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for root, dirs, files in os.walk(room_results_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, room_results_path)
                zf.write(file_path, arcname)
    
    memory_file.seek(0)
    return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name=f'room_{room_id}_results.zip')

@app.route('/download_task_file', methods=['GET'])
def download_task_file():
    room_id = request.args.get('room_id')
    if not room_id:
        return jsonify({"error": "Missing room_id"}), 400
    
    task_file_path = os.path.join(ROOMS_FOLDER, room_id, "log", "tasks.json")
    if not os.path.exists(task_file_path):
        return jsonify({"error": "Task file not found"}), 404
    
    return send_file(task_file_path, as_attachment=True)

@app.route('/check_room_status', methods=['GET'])
def check_room_status():
    room_id = request.args.get('room_id')
    try:
        status = room_manager.get_room_status(room_id)
        return jsonify(status)
    except Exception as e:
        app.logger.error(f"Error checking room status: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/list_final_files', methods=['GET'])
def list_final_files():
    room_id = request.args.get('room_id')
    if not room_id:
        return jsonify({"error": "Missing room_id"}), 400
    
    final_dir = os.path.join(ROOMS_FOLDER, room_id, "final")
    if not os.path.exists(final_dir):
        return jsonify({"files": []}), 200
    
    files = os.listdir(final_dir)
    return jsonify({"files": files}), 200

@app.route('/download_final_file', methods=['GET'])
def download_final_file():
    room_id = request.args.get('room_id')
    file_name = request.args.get('file_name')
    if not room_id or not file_name:
        return jsonify({"error": "Missing room_id or file_name"}), 400
    
    file_path = os.path.join(ROOMS_FOLDER, room_id, "final", file_name)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    
    return send_file(file_path, as_attachment=True)

@app.route('/get_tasks', methods=['GET'])
def get_tasks():
    room_id = request.args.get('room_id')
    if not room_id:
        return jsonify({"error": "Missing room_id"}), 400
    
    tasks = room_manager.get_tasks(room_id)
    return jsonify({"tasks": tasks}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5801)  # 移除 ssl_context='adhoc'