import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import socket
import os
import threading
from datetime import datetime

class FileServer:
    def __init__(self):
        # 初始化GUI窗口
        self.window = tk.Tk()
        self.window.title("文件传输服务器")
        self.window.geometry("600x500")
        self.window.configure(bg='#f0f0f0')
        
        # 创建主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 状态框架
        status_frame = ttk.LabelFrame(main_frame, text="服务器状态", padding="5")
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="未启动", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # IP地址显示
        self.ip_label = ttk.Label(status_frame, text=f"本机IP: {self.get_local_ip()}")
        self.ip_label.pack(side=tk.RIGHT, padx=5)
        
        # 文件选择框架
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding="5")
        file_frame.pack(fill=tk.X, pady=5)
        
        self.select_button = ttk.Button(file_frame, text="选择文件", command=self.select_file)
        self.select_button.pack(side=tk.LEFT, padx=5)

        self.file_label = ttk.Label(file_frame, text="未选择文件")
        self.file_label.pack(side=tk.LEFT, padx=5)
        
        # 传输模式框架 - 移到这里
        thread_frame = ttk.LabelFrame(main_frame, text="传输模式", padding="5")
        thread_frame.pack(fill=tk.X, pady=5)
        
        self.thread_var = tk.IntVar(value=1)
        ttk.Radiobutton(thread_frame, text="单线程传输", variable=self.thread_var, value=1).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(thread_frame, text="多线程传输(4线程)", variable=self.thread_var, value=4).pack(side=tk.LEFT, padx=5)
        
        # 控制框架
        control_frame = ttk.LabelFrame(main_frame, text="控制", padding="5")
        control_frame.pack(fill=tk.X, pady=5)
        
        self.start_button = ttk.Button(control_frame, text="启动服务器", command=self.start_server)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
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
        
        # 初始化变量
        self.selected_file = None
        self.server_socket = None
        self.chunk_size = 1024 * 1024  # 每个块1MB
        self.total_sent = 0
        self.lock = threading.Lock()  # 线程锁
    
    def get_local_ip(self):
        """
        获取本机IP地址

        Returns:
            str: 本机IP地址
        """
        try:
            # 创建UDP套接字 并不真正发送数据，只是利用套接字获取本地IP地址
            # AF_INET: IPv4协议     SOCK_DGRAM: UDP协议
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 此时套接字还没有绑定到任何具体的IP和端口

            # 连接到Google的DNS服务器
            # 8.8.8.8: Google的DNS服务器地址     80: HTTP默认端口号
            # 调用connect()方法，将套接字连接到指定的地址和端口
            # OS做的事情；
            # 1. 查看路由表，确定到达8.8.8.8需要使用哪个网卡
            # 2. 选择该网卡上的IP地址作为源地址
            # 3. 将套接字分配一个本地端口号
            s.connect(("8.8.8.8", 80))  # 连接到Google的DNS服务器
            
            ip = s.getsockname()[0]  # 获取本地IP地址
            s.close()  # 关闭套接字
            return ip
        except:
            return "127.0.0.1"  # 如果获取IP失败，返回本地回环地址
    

    def log_message(self, message):
        """
        记录日志

        Args:
            message (str): 日志消息
        """
        current_time = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{current_time}] {message}\n")
        self.log_text.see(tk.END) # 滚动到最新日志
    

    def select_file(self):
        """选择文件"""
        self.selected_file = filedialog.askopenfilename()  # 选择文件
        if self.selected_file:
            file_name = os.path.basename(self.selected_file)  # 获取文件名
            file_size = os.path.getsize(self.selected_file)  # 获取文件大小
            size_str = self.format_size(file_size)  # 格式化文件大小
            self.file_label.config(text=f"已选择: {file_name} ({size_str})")  # 更新文件标签
            self.log_message(f"已选择文件: {file_name}")  # 记录日志
    

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
    

    def send_file_chunk(self, client_socket, start_pos, chunk_size, thread_id):
        """
        发送文件块

        Args:
            client_socket (socket.socket): 客户端套接字
            start_pos (int): 开始位置
            chunk_size (int): 块大小
            thread_id (int): 线程ID

        Raises:
            FileNotFoundError: 文件不存在或已被移动
            PermissionError: 没有文件读取权限
            Exception: 文件读取不完整
            Exception: 网络超时
            Exception: 网络连接错误
            Exception: 发送数据超时
            Exception: 连接被客户端重置
        """
        try:
            if not os.path.exists(self.selected_file):
                raise FileNotFoundError("文件不存在或已被移动")
            
            if not os.access(self.selected_file, os.R_OK):
                raise PermissionError("没有文件读取权限")
            
            with open(self.selected_file, 'rb') as f:
                # 这里是每个线程独立读取文件
                f.seek(start_pos)  # 设置文件指针到开始位置
                data = f.read(chunk_size)  # 读取指定大小的数据
                
                if len(data) != chunk_size and thread_id != self.thread_var.get() - 1:
                    raise Exception("文件读取不完整")
                    
                # 使用固定长度的头部信息
                # 线程ID: 4位整数  数据长度: 10位整数
                header = f"{thread_id:04d}|{len(data):010d}".encode()

                # 将字节串左对齐，填充到20字节
                header = header.ljust(20, b' ')
                
                try:
                    # 设置超时
                    client_socket.settimeout(10)  # 10秒超时
                    
                    # 先发送头部，再发送数据
                    client_socket.sendall(header)
                    
                    # 等待确认，带超时
                    if not client_socket.recv(1):
                        raise Exception("客户端未确认接收")
                    
                    # 分块发送数据
                    total_sent = 0
                    buffer_size = 8192  # 缓冲区大小，8192B = 8KB
                    while total_sent < len(data):
                        try:
                            end = min(total_sent + buffer_size, len(data))
                            client_socket.sendall(data[total_sent:end])
                            total_sent = end
                        except socket.timeout:
                            raise Exception("发送数据超时")
                        except ConnectionResetError:
                            raise Exception("连接被客户端重置")
                    
                    # 使用锁：保护共享资源
                    with self.lock:
                        self.total_sent += len(data)
                        progress = (self.total_sent / self.file_size) * 100
                        self.progress_bar['value'] = self.total_sent
                        self.progress_label.config(
                            text=f"传输进度: {progress:.2f}% ({self.format_size(self.total_sent)}/{self.format_size(self.file_size)})"
                        )

                    self.log_message(f"线程{thread_id}完成传输: {self.format_size(len(data))}")
                    
                except socket.timeout:
                    raise Exception("网络超时")
                except ConnectionError:
                    raise Exception("网络连接错误")
                finally:
                    client_socket.settimeout(None)  # 恢复默认超时设置
                    
        except Exception as e:
            self.log_message(f"线程{thread_id}传输错误: {str(e)}")
            raise  # 重新抛出异常，确保主线程知道传输失败
    

    def start_server(self):
        """启动服务器"""
        if not self.selected_file:
            messagebox.showerror("错误", "请先选择要传输的文件！")
            return
        
        if not os.path.exists(self.selected_file):
            messagebox.showerror("错误", "文件不存在或已被移动！")
            return
        
        if os.path.getsize(self.selected_file) == 0:
            messagebox.showerror("错误", "不能传输空文件！")
            return
        
        def server_thread():
            """
            服务器线程

            Raises:
                ValueError: 线程数必须大于0
                Exception: 等待客户端连接超时
                Exception: 等待客户端连接超时
            """
            try:
                thread_count = self.thread_var.get()  # 获取线程数
                if thread_count <= 0:
                    raise ValueError("线程数必须大于0")
                
                # 创建套接字，使用IPv4协议，TCP协议
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # 设置套接字选项，允许重用地址
                # 允许重用：当服务器程序关闭时，OS会将端口保持在TIME_WAIT状态，
                # 此时如果重启服务器，新创建的套接字可能会因为端口被占用而失败
                # 设置SO_REUSEADDR选项，可以让OS在TIME_WAIT状态下立即重用该端口
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                
                try:
                    # 0.0.0.0: 表示监听所有网卡上的所有IP地址
                    # 9999: 监听的端口号
                    self.server_socket.bind(('0.0.0.0', 9999))  # 绑定到0.0.0.0:9999
                except OSError as e:
                    if e.errno == 98:  # 地址已被使用
                        raise Exception("端口9999已被占用，请关闭其他服务器实例")
                    raise
                
                # 监听连接，最多允许thread_count个连接
                self.server_socket.listen(thread_count)
                self.status_label.config(text="等待连接...", foreground="orange")
                self.log_message("服务器已启动，等待客户端连接...")
                
                # 设置accept超时
                self.server_socket.settimeout(60)  # 60秒超时
                try:
                    # 从连接队列中取出一个客户端连接请求
                    # 创建一个新套接字，用于与客户端通信
                    # 返回一个新套接字和客户端地址
                    main_socket, addr = self.server_socket.accept()
                except socket.timeout:
                    raise Exception("等待客户端连接超时")
                
                # 发送文件信息
                file_name = os.path.basename(self.selected_file)
                self.file_size = os.path.getsize(self.selected_file)
                file_info = f"{file_name}|{self.file_size}|{thread_count}".encode()
                main_socket.send(file_info)
                main_socket.recv(1024)  # 等待客户端确认，1024为缓冲区大小
                
                self.total_sent = 0
                self.progress_bar['maximum'] = self.file_size
                
                if thread_count == 1:
                    # 单线程传输
                    self.send_file_chunk(main_socket, 0, self.file_size, 0)
                    main_socket.close()
                else:
                    # 多线程传输
                    chunk_size = self.file_size // thread_count
                    threads = []
                    sockets = []

                    # 等待所有数据连接建立
                    for i in range(thread_count):
                        data_socket, _ = self.server_socket.accept()
                        sockets.append(data_socket)
                        self.log_message(f"数据连接 {i} 已建立")

                    for i in range(thread_count):
                        start_pos = i * chunk_size
                        # 最后一个线程处理剩余所有数据
                        if i == thread_count - 1:
                            chunk_size = self.file_size - start_pos
                        
                        # 创建线程，每个线程独立读取文件
                        thread = threading.Thread(
                            target=self.send_file_chunk,
                            args=(sockets[i], start_pos, chunk_size, i)
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
                
                self.progress_label.config(text="传输完成！")
                self.log_message("文件传输完成")
                self.server_socket.close()
                
            except Exception as e:
                messagebox.showerror("错误", f"传输出错：{str(e)}")
                self.status_label.config(text="出错", foreground="red")
                self.log_message(f"错误: {str(e)}")
            finally:
                try:
                    if hasattr(self, 'server_socket'):
                        self.server_socket.close()
                except:
                    pass
        
        threading.Thread(target=server_thread).start()
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    server = FileServer()
    server.run() 