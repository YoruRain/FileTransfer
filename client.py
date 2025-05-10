import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import socket
import os
import threading
from datetime import datetime
import time

class FileClient:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("文件传输客户端")
        self.window.geometry("600x500")
        self.window.configure(bg='#f0f0f0')
        
        # 创建主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 连接框架
        connect_frame = ttk.LabelFrame(main_frame, text="服务器连接", padding="5")
        connect_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(connect_frame, text="服务器IP:").pack(side=tk.LEFT, padx=5)
        
        self.ip_entry = ttk.Entry(connect_frame, width=15)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        
        self.connect_button = ttk.Button(connect_frame, text="连接服务器", command=self.connect_server)
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(connect_frame, text="未连接", foreground="red")
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # 文件信息框架
        file_frame = ttk.LabelFrame(main_frame, text="文件信息", padding="5")
        file_frame.pack(fill=tk.X, pady=5)
        
        self.file_info_label = ttk.Label(file_frame, text="等待接收文件...")
        self.file_info_label.pack(pady=5)
        
        # 进度框架
        progress_frame = ttk.LabelFrame(main_frame, text="传输进度", padding="5")
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, length=300, mode='determinate')
        self.progress_bar.pack(pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="等待传输...")
        self.progress_label.pack(pady=5)
        
        # 日志框架
        log_frame = ttk.LabelFrame(main_frame, text="传输日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, width=50)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # 设置样式
        style = ttk.Style()
        style.configure('TButton', padding=5)
        style.configure('TLabelframe', background='#f0f0f0')
        
        self.received_chunks = {}
        self.lock = threading.Lock()
        self.total_received = 0
    
    def log_message(self, message):
        """
        记录日志

        Args:
            message (str): 日志消息
        """
        current_time = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{current_time}] {message}\n")
        self.log_text.see(tk.END)
    

    def format_size(self, size):
        """
        格式化文件大小

        Args:
            size (int): 文件大小

        Returns:
            str: 格式化后的文件大小
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
    
    def receive_chunk(self, client_socket, thread_id, save_file):
        """
        接收文件数据块

        Args:
            client_socket (socket.socket): 客户端套接字
            thread_id (int): 线程ID
            save_file (file): 保存文件
        """
        try:
            client_socket.settimeout(10)  # 10秒超时
            
            # 接收固定长度的头部信息
            header = b""
            try:
                while len(header) < 20:
                    chunk = client_socket.recv(20 - len(header))
                    if not chunk:
                        raise Exception("连接中断")
                    header += chunk
            except socket.timeout:
                raise Exception("接收头部信息超时")
            
            try:
                header = header.decode().strip()
                thread_id, chunk_size = map(int, header.split('|'))
            except (UnicodeDecodeError, ValueError):
                raise Exception("头部信息格式错误")
            
            if chunk_size <= 0:
                raise ValueError("无效的数据块大小")
            
            client_socket.send(b'1')  # 发送确认
            
            # 接收数据块
            received_data = bytearray()  # 可变字节序列，存储二进制数据
            remaining = chunk_size
            last_progress_time = time.time()
            
            while remaining > 0:
                try:
                    buffer_size = min(remaining, 8192)
                    data = client_socket.recv(buffer_size)
                    if not data:
                        raise Exception("连接中断")
                    received_data.extend(data)
                    remaining -= len(data)
                    
                    # 检查传输是否停滞
                    current_time = time.time()
                    if current_time - last_progress_time > 30:  # 30秒无进展
                        raise Exception("传输停滞")
                    if data:
                        last_progress_time = current_time
                        
                except socket.timeout:
                    raise Exception("接收数据超时")
            
            if len(received_data) != chunk_size:
                raise Exception(f"数据不完整: 预期{chunk_size}字节，实际接收{len(received_data)}字节")
            
            try:
                # 线程锁，保护共享资源
                with self.lock:
                    save_file.seek(thread_id * self.chunk_size)
                    save_file.write(received_data)
                    self.total_received += len(received_data)
                    progress = (self.total_received / self.file_size) * 100
                    self.progress_bar['value'] = self.total_received
                    self.progress_label.config(
                        text=f"接收进度: {progress:.2f}% ({self.format_size(self.total_received)}/{self.format_size(self.file_size)})"
                    )
            except IOError as e:
                raise Exception(f"写入文件错误: {str(e)}")
            
            self.log_message(f"线程{thread_id}接收完成: {self.format_size(len(received_data))}")
        
        except Exception as e:
            self.log_message(f"线程{thread_id}接收错误: {str(e)}")
            raise
        finally:
            client_socket.settimeout(None)
    

    def connect_server(self):
        """连接服务器"""
        def connect_thread():
            """连接服务器线程"""
            try:
                # 主连接用于交换控制信息
                main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_ip = self.ip_entry.get()
                self.log_message(f"正在连接服务器 {server_ip}...")
                main_socket.connect((server_ip, 9999))
                self.status_label.config(text="已连接", foreground="green")
                self.log_message("已连接到服务器")
                
                # 接收文件信息
                file_info = main_socket.recv(1024).decode()
                file_name, file_size, thread_count = file_info.split('|')
                self.file_size = int(file_size)
                thread_count = int(thread_count)
                
                self.file_info_label.config(
                    text=f"文件名: {file_name} (大小: {self.format_size(self.file_size)}, 线程数: {thread_count})"
                )
                self.log_message(f"准备接收文件: {file_name}")
                
                # 选择保存位置
                save_path = filedialog.asksaveasfilename(
                    defaultextension=os.path.splitext(file_name)[1],
                    initialfile=file_name,
                    title="选择保存位置"
                )
                
                if not save_path:
                    self.log_message("用户取消接收")
                    main_socket.close()
                    return
                
                # 创建空文件
                with open(save_path, 'wb') as f:
                    f.seek(self.file_size - 1)
                    f.write(b'\0')  # 写入空字节，确保文件大小正确
                
                main_socket.send(b"ready")  # 通知服务器准备就绪
                
                self.total_received = 0
                self.progress_bar['maximum'] = self.file_size
                self.chunk_size = self.file_size // thread_count
                
                # 开始接收文件
                with open(save_path, 'r+b') as save_file:
                    if thread_count == 1:
                        # 单线程接收
                        self.receive_chunk(main_socket, 0, save_file)
                        main_socket.close()
                    else:
                        # 多线程接收：为每个线程创建独立的socket连接
                        threads = []
                        sockets = []
                        
                        # 创建数据连接
                        for i in range(thread_count):
                            # 创建数据连接，使用IPv4协议，TCP协议
                            data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            data_socket.connect((server_ip, 9999))
                            sockets.append(data_socket)
                            self.log_message(f"数据连接 {i} 已建立")
                        
                        for i in range(thread_count):
                            thread = threading.Thread(
                                target=self.receive_chunk,
                                args=(sockets[i], i, save_file)
                            )
                            threads.append(thread)
                            thread.start()
                        
                        # 等待所有线程完成
                        for thread in threads:
                            thread.join()
                        
                        # 关闭所有数据连接
                        for sock in sockets:
                            sock.close()
                        main_socket.close()
                
                self.progress_label.config(text="接收完成！")
                self.log_message(f"文件保存至: {save_path}")
                
            except Exception as e:
                messagebox.showerror("错误", f"接收出错：{str(e)}")
                self.status_label.config(text="出错", foreground="red")
                self.log_message(f"错误: {str(e)}")
        
        threading.Thread(target=connect_thread).start()
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    client = FileClient()
    client.run() 