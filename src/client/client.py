import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox

clients = []  # 用于存储连接的客户端

def handle_client(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')  # 接收来自客户端的消息
            if message:
                broadcast(message, client_socket)  # 广播消息
                update_chat(f"Received: {message}")  # 更新聊天记录
            else:
                break
        except:
            break

    client_socket.close()
    clients.remove(client_socket)
    update_chat("A client has disconnected.")

def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:  # 不发送给发送者
            try:
                client.send(message.encode('utf-8'))  # 发送消息
            except:
                client.close()
                clients.remove(client)

def start_server(host='0.0.0.0', port=12345):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建socket对象
    server.bind((host, port))  # 绑定地址和端口
    server.listen(5)  # 启动监听
    update_chat(f"Server listening on {host}:{port}")

    while True:
        client_socket, addr = server.accept()  # 接受客户端连接
        clients.append(client_socket)  # 添加到客户端列表
        update_chat(f"Accepted connection from {addr}")
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()  # 启动线程处理客户端

def update_chat(message):
    chat_area.configure(state='normal')
    chat_area.insert(tk.END, message + "\n")
    chat_area.configure(state='disabled')
    chat_area.yview(tk.END)  # 自动滚动到最后一行

def start_server_thread():
    threading.Thread(target=start_server, daemon=True).start()

# 创建GUI
root = tk.Tk()
root.title("3306 Server")
root.geometry("500x400")

frame = ttk.Frame(root)
frame.pack(padx=10, pady=10, fill='both', expand=True)

chat_area = tk.Text(frame, wrap='word', state='disabled', height=15)
chat_area.pack(padx=5, pady=5, fill='both', expand=True)

start_button = ttk.Button(root, text="Start Server", command=start_server_thread)
start_button.pack(pady=(5, 0))

root.mainloop()
