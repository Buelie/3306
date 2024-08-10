import socket
import threading
import tkinter as tk
from tkinter import ttk
import asyncio
import websockets

# 多语言支持
translations = {
    'en': {
        'tcp_host': 'TCP Host:',
        'tcp_port': 'TCP Port:',
        'ws_port': 'WebSocket Port:',
        'start_tcp': 'Start TCP Server',
        'start_ws': 'Start WebSocket Server',
        'stop_servers': 'Stop Servers',
        'server_listening': 'Server listening on',
        'client_connected': 'Accepted connection from',
        'client_disconnected': 'A TCP client has disconnected.',
        'websocket_disconnected': 'A WebSocket client has disconnected.',
        'tcp_server_stopped': 'TCP Server stopped.',
        'ws_server_stopped': 'WebSocket Server stopped. Please restart the application to stop WebSocket server.',
        'select_language': 'Select Language:',  # 新增翻译
    },
    'zh': {
        'tcp_host': 'TCP 主机:',
        'tcp_port': 'TCP 端口:',
        'ws_port': 'WebSocket 端口:',
        'start_tcp': '启动 TCP 服务器',
        'start_ws': '启动 WebSocket 服务器',
        'stop_servers': '停止服务器',
        'server_listening': '服务器监听在',
        'client_connected': '接受来自的连接',
        'client_disconnected': '一个 TCP 客户端已断开连接。',
        'websocket_disconnected': '一个 WebSocket 客户端已断开连接。',
        'tcp_server_stopped': 'TCP 服务器已停止。',
        'ws_server_stopped': 'WebSocket 服务器已停止。请重新启动应用程序以停止 WebSocket 服务器。',
        'select_language': '选择语言:',  # 新增翻译
    },
    'ru': {
        'tcp_host': 'TCP Хост:',
        'tcp_port': 'TCP Порт:',
        'ws_port': 'WebSocket Порт:',
        'start_tcp': 'Запустить TCP сервер',
        'start_ws': 'Запустить WebSocket сервер',
        'stop_servers': 'Остановить серверы',
        'server_listening': 'Сервер слушает на',
        'client_connected': 'Принято соединение от',
        'client_disconnected': 'TCP клиент отключился.',
        'websocket_disconnected': 'WebSocket клиент отключился.',
        'tcp_server_stopped': 'TCP сервер остановлен.',
        'ws_server_stopped': 'WebSocket сервер остановлен. Пожалуйста, перезапустите приложение, чтобы остановить WebSocket сервер.',
        'select_language': 'Выберите язык:',  # 新增翻译
    }
}

current_language = 'en'  # 默认语言

clients = []  # 用于存储TCP连接的客户端
websocket_clients = []  # 用于存储WebSocket连接的客户端
tcp_server = None
ws_server = None

# 处理TCP客户端
def handle_client(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')  # 接收来自客户端的消息
            if message:
                broadcast(message, client_socket)  # 广播消息
                update_chat(f"{translations[current_language]['client_connected']}: {message}")  # 更新聊天记录
            else:
                break
        except Exception as e:
            print(f"Error: {e}")
            break

    client_socket.close()
    clients.remove(client_socket)
    update_chat(translations[current_language]['client_disconnected'])

# 广播消息到TCP客户端
def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:  # 不发送给发送者
            try:
                client.send(message.encode('utf-8'))  # 发送消息
            except Exception as e:
                print(f"Error: {e}")
                client.close()
                clients.remove(client)

async def websocket_handler(websocket, path):
    websocket_clients.append(websocket)
    try:
        async for message in websocket:
            await broadcast_websocket(message)  # 广播消息
            update_chat(f"WebSocket {translations[current_language]['client_connected']}: {message}")  # 更新聊天记录
    finally:
        websocket_clients.remove(websocket)
        update_chat(translations[current_language]['websocket_disconnected'])

# 广播消息到WebSocket客户端
async def broadcast_websocket(message):
    for websocket in websocket_clients:
        await websocket.send(message)  # 发送消息给所有WebSocket客户端

# 启动TCP服务器
def start_server(host='0.0.0.0', port=12345):
    global tcp_server
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建socket对象
    tcp_server.bind((host, port))  # 绑定地址和端口
    tcp_server.listen(5)  # 启动监听
    update_chat(f"{translations[current_language]['server_listening']} {host}:{port}")

    while True:
        client_socket, addr = tcp_server.accept()  # 接受客户端连接
        clients.append(client_socket)  # 添加到TCP客户端列表
        update_chat(f"{translations[current_language]['client_connected']} {addr}")
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()  # 启动线程处理TCP客户端

# 启动WebSocket服务器
async def start_websocket_server(host='0.0.0.0', port=8765):
    global ws_server
    ws_server = await websockets.serve(websocket_handler, host, port)
    update_chat(f"{translations[current_language]['server_listening']} {host}:{port}")
    await ws_server.wait_closed()

# 更新聊天区域
def update_chat(message):
    chat_area.configure(state='normal')
    chat_area.insert(tk.END, message + "\n")
    chat_area.configure(state='disabled')
    chat_area.yview(tk.END)  # 自动滚动到最后一行

# 启动TCP服务器线程
def start_server_thread():
    host = host_entry.get()
    port = int(port_entry.get())
    threading.Thread(target=start_server, args=(host, port), daemon=True).start()

# 启动WebSocket服务器线程
def start_websocket_server_thread():
    host = host_entry.get()
    port = int(ws_port_entry.get())
    threading.Thread(target=asyncio.run, args=(start_websocket_server(host, port),), daemon=True).start()

# 关闭服务器
def stop_servers():
    global tcp_server, ws_server
    if tcp_server:
        tcp_server.close()
        update_chat(translations[current_language]['tcp_server_stopped'])
    if ws_server:
        # 这里没有直接关闭WebSocket服务器的API
        update_chat(translations[current_language]['ws_server_stopped'])
    # 清空客户端列表
    clients.clear()
    websocket_clients.clear()

# 创建语言选择
def change_language(lang):
    global current_language
    current_language = lang
    update_texts()

# 更新界面文本
def update_texts():
    host_label.config(text=translations[current_language]['tcp_host'])
    port_label.config(text=translations[current_language]['tcp_port'])
    ws_port_label.config(text=translations[current_language]['ws_port'])
    start_button.config(text=translations[current_language]['start_tcp'])
    start_ws_button.config(text=translations[current_language]['start_ws'])
    stop_button.config(text=translations[current_language]['stop_servers'])
    language_label.config(text=translations[current_language]['select_language'])  # 更新语言标签文本

# 创建GUI
root = tk.Tk()
root.title("3306 Server")
root.geometry("700x400")  # 设置窗口大小为700x400

frame = ttk.Frame(root)
frame.pack(padx=10, pady=10, fill='both', expand=True)

chat_area = tk.Text(frame, wrap='word', state='disabled', height=15)
chat_area.pack(padx=5, pady=5, fill='both', expand=True)

# 创建输入框以获取服务器地址和端口
input_frame = ttk.Frame(root)
input_frame.pack(pady=(5, 0))

host_label = ttk.Label(input_frame, text=translations[current_language]['tcp_host'])
host_label.grid(row=0, column=0, padx=5, pady=5)
host_entry = ttk.Entry(input_frame)
host_entry.insert(0, '0.0.0.0')  # 默认值
host_entry.grid(row=0, column=1, padx=5, pady=5)

port_label = ttk.Label(input_frame, text=translations[current_language]['tcp_port'])
port_label.grid(row=1, column=0, padx=5, pady=5)
port_entry = ttk.Entry(input_frame)
port_entry.insert(0, '12345')  # 默认值
port_entry.grid(row=1, column=1, padx=5, pady=5)

ws_port_label = ttk.Label(input_frame, text=translations[current_language]['ws_port'])
ws_port_label.grid(row=2, column=0, padx=5, pady=5)
ws_port_entry = ttk.Entry(input_frame)
ws_port_entry.insert(0, '8765')  # 默认值
ws_port_entry.grid(row=2, column=1, padx=5, pady=5)

# 创建按钮框架
button_frame = ttk.Frame(root)
button_frame.pack(pady=(5, 10))

start_button = ttk.Button(button_frame, text=translations[current_language]['start_tcp'], command=start_server_thread)
start_button.pack(side=tk.LEFT, padx=5)

start_ws_button = ttk.Button(button_frame, text=translations[current_language]['start_ws'], command=start_websocket_server_thread)
start_ws_button.pack(side=tk.LEFT, padx=5)

stop_button = ttk.Button(button_frame, text=translations[current_language]['stop_servers'], command=stop_servers)
stop_button.pack(side=tk.LEFT, padx=5)

# 语言选择下拉框
language_frame = ttk.Frame(root)
language_frame.pack(pady=(5, 10))

language_label = ttk.Label(language_frame, text=translations[current_language]['select_language'])  # 使用新增的翻译
language_label.pack(side=tk.LEFT)

language_selector = ttk.Combobox(language_frame, values=["English", "中文", "Русский"], state='readonly')
language_selector.set("English")
language_selector.bind('<<ComboboxSelected>>', lambda event: change_language('en' if language_selector.get() == "English" else 'zh' if language_selector.get() == "中文" else 'ru'))
language_selector.pack(side=tk.LEFT)

# 运行Tkinter主循环
root.mainloop()
