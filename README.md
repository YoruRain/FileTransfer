# 计算机网络课程设计：网络文件传输

## 设计目的

掌握实现网络文件传输的方法，并了解TCP 连接是基于字节流的；而UDP 连接是不可靠的，以及如何提高其可靠性。

## 设计要求

1. 实现单线程文件传输功能；
2. 在以上基础上，掌握多线程技术，在文件网络传输时，可选择单线程或多线程；
3. 加入异常控制依据，增强程序的鲁棒性（Robust）；
4. 了解如何提高套接字传输的速率，以及如何加强传输的稳定性。

## 设计内容

1. 服务器端（负责发送数据）设计
2. 客户端（负责接收数据）设计

## 思考题

1. 套接字有基于阻塞和非阻塞的工作方式，试问你编写的程序是基于阻塞还是非阻塞的？各有什么优缺点？
    答：

    阻塞式实现。特征：

    - 服务器使用`socket.accept()`阻塞等待客户端连接
    - 使用`socket.recv()`接收数据时会阻塞等待
    - 使用`socket.send()`发送数据时会阻塞直到数据发送完毕

    阻塞式：

    优点：

    - 编程模型简单直观
    - 代码逻辑清晰
    - 按顺序执行，容易理解

    缺点：

    - I/O操作时会阻塞线程
    - 需要多线程来处理并发
    - 在高并发场景下性能较差

    非阻塞式：

    优点：

    - 单线程可处理多个连接
    - 更好的并发性能
    - 资源利用率更高

    缺点：

    - 编程模型复杂
    - 需要额外的时间循环处理
    - 错误处理更复杂

2. 如何将上述通信改为非阻塞，避免阻塞？
    答：
    可以通过以下方式改造为非阻塞：

    ```python
    # 1. 设置套接字为非阻塞模式
    server_socket.setblocking(False)

    # 2. 使用 select/poll/epoll 进行 I/O 多路复用
    import select

    # 创建 epoll 对象
    epoll = select.epoll()
    epoll.register(server_socket.fileno(), select.EPOLLIN)

    while True:
        events = epoll.poll(1)
        for fileno, event in events:
            if fileno == server_socket.fileno():
                # 处理新连接
                client_socket, addr = server_socket.accept()
                client_socket.setblocking(False)
                epoll.register(client_socket.fileno(), select.EPOLLIN)
            else:
                # 处理数据
                try:
                    data = client_socket.recv(1024)
                    if data:
                        # 处理数据
                        pass
                    else:
                        # 连接关闭
                        epoll.unregister(fileno)
                        client_socket.close()
                except socket.error:
                    continue
    ```

3. 在传输前能否先将要传输的文件的相关属性现行报告给对方，以便对方判断是否接受该文件的传输？
    答：

    当前程序已经实现：

    ```python
    # 服务器端发送文件信息
    file_info = f"{file_name}|{self.file_size}|{thread_count}".encode()
    main_socket.send(file_info)

    # 客户端接收并处理文件信息
    file_info = main_socket.recv(1024).decode()
    file_name, file_size, thread_count = file_info.split('|')
    ```

4. 了解并熟悉多线程工作原理，试编写基于多线程的网络文件传输程序。    答：

    当前程序已经实现多线程工作原理。

    - 使用`threading.Thread()`创建多个传输线程
    - 使用`threading.Lock()`实现线程同步，保护共享资源