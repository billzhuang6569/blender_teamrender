import os
import subprocess
import sys
import traceback
import psutil

def get_project_dir():
    if getattr(sys, 'frozen', False):
        dir = os.path.dirname(sys.executable)
        print(f"运行的是打包后的exe文件，目录为: {dir}")
    else:
        dir = os.path.dirname(os.path.abspath(__file__))
        print(f"运行的是Python脚本，目录为: {dir}")
    return dir

def run_python_script(python_path, script_path):
    print(f"Python解释器路径: {python_path}")
    print(f"执行的脚本: {script_path}")
    try:
        result = subprocess.run([python_path, script_path], capture_output=True, text=True, check=True)
        print(f"脚本输出:\n{result.stdout}")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"执行脚本时出错:\n{e.stderr}")
        return e.returncode

def check_server():
    project_dir = get_project_dir()
    check_server_script = os.path.join(project_dir, 'app', 'check_server.py')
    python_path = os.path.join(project_dir, '.venv', 'Scripts', 'python.exe')
    
    print("正在检查服务器状态...")
    return_code = run_python_script(python_path, check_server_script)
    return return_code == 0

def kill_process_on_port(port):
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.pid != 0:
            try:
                process = psutil.Process(conn.pid)
                process.terminate()
                print(f"已终止使用端口 {port} 的进程 (PID: {conn.pid})")
                return True
            except psutil.NoSuchProcess:
                print(f"进程 (PID: {conn.pid}) 不存在")
            except psutil.AccessDenied:
                print(f"无权限终止进程 (PID: {conn.pid})")
            except Exception as e:
                print(f"终止进程 (PID: {conn.pid}) 时发生错误: {str(e)}")
    print(f"没有找到使用端口 {port} 的可终止进程")
    return False

def exit_handler():
    print("正在关闭程序...")
    current_process = psutil.Process()
    children = current_process.children(recursive=True)
    for child in children:
        try:
            child.terminate()
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            print(f"无权限终止子进程 (PID: {child.pid})")
        except Exception as e:
            print(f"终止子进程 (PID: {child.pid}) 时发生错误: {str(e)}")
    psutil.wait_procs(children, timeout=5)

try:
    # 在开始时尝试释放端口
    if kill_process_on_port(7860):
        print("已释放端口 7860")
    else:
        print("端口 7860 未被占用或无法释放")

    project_dir = get_project_dir()
    print(f"项目目录: {project_dir}")

    # 切换到项目目录
    os.chdir(project_dir)
    print(f"当前工作目录: {os.getcwd()}")

    # 虚拟环境中Python解释器的路径
    python_path = os.path.join(project_dir, '.venv', 'Scripts', 'python.exe')
    if not os.path.exists(python_path):
        print(f"错误: Python解释器不存在于 {python_path}")
        sys.exit(1)
    
    # web.py的路径
    web_script = os.path.join(project_dir, 'web.py')
    if not os.path.exists(web_script):
        print(f"错误: web.py不存在于 {web_script}")
        sys.exit(1)

    # 检查服务器状态
    if check_server():
        print("服务器状态正常，正在启动web.py...")
        return_code = run_python_script(python_path, web_script)

        if return_code == 0:
            print("web.py已成功启动。")
        else:
            print(f"启动web.py时出现错误。返回码: {return_code}")
    else:
        print("服务器状态异常，不启动web.py。")

except Exception as e:
    print(f"发生错误: {str(e)}")
    print("错误详情:")
    traceback.print_exc()

finally:
    input("按回车键关闭此窗口...")
    exit_handler()