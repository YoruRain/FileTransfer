import client
import server
import threading
# import time

def run_server():
    """运行服务器"""
    server_instance = server.FileServer()
    server_instance.run()

def run_client():
    """运行客户端"""
    client_instance = client.FileClient()
    client_instance.run()

# 使用守护线程运行服务器，主线程运行客户端
if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True  # # 设置为守护线程，主线程结束时自动终止
    server_thread.start()

    run_client()
