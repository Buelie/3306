import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import uuid  # 导入uuid模块以生成唯一ID

class ChatClient:
    def __init__(self, master):
        self.master = master
        self.master.title("3306 客户端")  # "3306 Client" translated
        win_width = 900
        win_height = 800
        screen_width, screen_height = self.master.maxsize()
        x = int((screen_width - win_width) / 2)
        y = int((screen_height - win_height) / 4)
        self.master.geometry("%sx%s+%s+%s" % (win_width, win_height, x, y))
        self.master.resizable(False, False)  # 禁用最小化按钮，允许垂直调整大小
        self.language = 'en'
        self.nickname = ""
        self.user_id = None  # 用于存储用户唯一ID
        self.sent_messages = []  # 存储发送的消息
        self.reply_to_message = None  # 当前回复的消息

        self.create_widgets()
        self.client_socket = None
        self.is_connected = False

    def create_widgets(self):
        style = ttk.Style()
        style.configure('TButton', padding=6)
        style.configure('TLabel', padding=6)

        connection_frame = ttk.LabelFrame(self.master, text=self.get_text('connection'), padding=(10, 10))
        connection_frame.pack(padx=10, pady=10, fill='x')

        self.nickname_label = ttk.Label(connection_frame, text=self.get_text('nickname'))
        self.nickname_label.grid(row=0, column=0, pady=(10, 0), sticky=tk.W)

        entry_width = 20
        self.nickname_entry = ttk.Entry(connection_frame, width=entry_width)
        self.nickname_entry.grid(row=0, column=1, pady=(10, 0), padx=(0, 10))

        self.address_label = ttk.Label(connection_frame, text=self.get_text('server_address'))
        self.address_label.grid(row=1, column=0, pady=(10, 0), sticky=tk.W)

        self.address_entry = ttk.Entry(connection_frame, width=entry_width)
        self.address_entry.grid(row=1, column=1, pady=(10, 0), padx=(0, 10))
        self.address_entry.insert(0, "127.0.0.1")  # 设置默认地址为本地地址

        self.port_label = ttk.Label(connection_frame, text=self.get_text('port'))
        self.port_label.grid(row=2, column=0, pady=(10, 0), sticky=tk.W)

        self.port_entry = ttk.Entry(connection_frame, width=entry_width)
        self.port_entry.grid(row=2, column=1, pady=(10, 0), padx=(0, 10))
        self.port_entry.insert(0, "12345")  # 设置默认端口为12345

        self.connect_button = ttk.Button(connection_frame, text=self.get_text('connect'), command=self.connect_to_server)
        self.connect_button.grid(row=3, columnspan=2, pady=(10, 0))

        self.export_button = ttk.Button(connection_frame, text=self.get_text('export_chat'), command=self.export_chat_history)
        self.export_button.grid(row=0, column=6, pady=(10, 0))

        self.info_button = ttk.Button(connection_frame, text=self.get_text('program_info'), command=self.show_program_info)
        self.info_button.grid(row=0, column=5, pady=(10, 0))

        self.status_label = ttk.Label(connection_frame, text=self.get_text('status_disconnected'), foreground='red')
        self.status_label.grid(row=4, columnspan=2, pady=(10, 0))

        # 新增用于显示用户ID的标签
        self.user_id_label = ttk.Label(connection_frame, text="User ID: Not Connected", foreground='blue')
        self.user_id_label.grid(row=5, columnspan=2, pady=(10, 0))

        # 新增用于查询用户ID的标签和输入框
        self.query_user_id_frame = ttk.LabelFrame(self.master, text=self.get_text('query_user_id'), padding=(10, 10))
        self.query_user_id_frame.pack(padx=10, pady=(0, 10), fill='x')

        self.query_nickname_label = ttk.Label(self.query_user_id_frame, text=self.get_text('nickname'))
        self.query_nickname_label.grid(row=0, column=0, pady=(10, 0), sticky=tk.W)

        self.query_nickname_entry = ttk.Entry(self.query_user_id_frame, width=entry_width)
        self.query_nickname_entry.grid(row=0, column=1, pady=(10, 0), padx=(0, 10))

        self.query_user_id_button = ttk.Button(self.query_user_id_frame, text=self.get_text('query_user_id'), command=self.query_user_id)
        self.query_user_id_button.grid(row=0, column=2, pady=(10, 0))

        self.chat_frame = ttk.LabelFrame(self.master, text=self.get_text('chat_area'), padding=(10, 10))
        self.chat_frame.pack(padx=10, pady=(0, 10), fill='both', expand=True)

        self.text_area = tk.Text(self.chat_frame, wrap='word', state='disabled', height=15)
        self.text_area.pack(padx=5, pady=5, fill='both', expand=True)

        self.private_message_frame = ttk.LabelFrame(self.master, text=self.get_text('private_message'), padding=(10, 10))
        self.private_message_frame.pack(padx=10, pady=(0, 10), fill='x')

        self.private_nickname_label = ttk.Label(self.private_message_frame, text=self.get_text('private_nickname'))
        self.private_nickname_label.grid(row=0, column=0, pady=(10, 0), sticky=tk.W)

        self.private_nickname_entry = ttk.Entry(self.private_message_frame, width=15)
        self.private_nickname_entry.grid(row=0, column=1, pady=(10, 0), padx=(0, 10))

        self.private_message_entry = ttk.Entry(self.private_message_frame, width=50)
        self.private_message_entry.grid(row=0, column=2, pady=(10, 0), padx=(0, 10))

        self.send_private_button = ttk.Button(self.private_message_frame, text=self.get_text('send_private'), command=self.send_private_message)
        self.send_private_button.grid(row=0, column=3, padx=(10, 0))

        self.input_frame = ttk.Frame(self.master)
        self.input_frame.pack(padx=10, pady=(0, 10), fill='x')

        self.entry = ttk.Entry(self.input_frame, width=30)
        self.entry.pack(side=tk.LEFT, padx=(0, 10), fill='x', expand=True)

        self.entry.bind('<Return>', lambda event: self.send_message())

        self.send_button = ttk.Button(self.input_frame, text=self.get_text('send'), command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)

        self.file_button = ttk.Button(self.input_frame, text=self.get_text('send_file'), command=self.send_file)
        self.file_button.pack(side=tk.RIGHT, padx=(10, 0))

        self.send_file_to_user_button = ttk.Button(self.input_frame, text=self.get_text('send_file_to_user'), command=self.send_file_to_user)
        self.send_file_to_user_button.pack(side=tk.RIGHT, padx=(10, 0))

        self.reply_button = ttk.Button(self.input_frame, text=self.get_text('reply'), command=self.reply_to_last_message)
        self.reply_button.pack(side=tk.RIGHT, padx=(10, 0))

        self.recall_button = ttk.Button(self.input_frame, text=self.get_text('recall'), command=self.recall_last_message)
        self.recall_button.pack(side=tk.RIGHT)

        self.language_menu = ttk.Combobox(self.input_frame, values=["English", "中文", "Русский", "Français", "Español", "Deutsch", "日本語", "한국어"], state='readonly', width=10)
        self.language_menu.set("English")
        self.language_menu.bind('<<ComboboxSelected>>', self.change_language)
        self.language_menu.pack(side=tk.RIGHT, padx=(10, 0))

        # 添加表情按钮
        self.emoji_button = ttk.Button(self.input_frame, text="😊", command=self.open_emoji_menu)
        self.emoji_button.pack(side=tk.RIGHT)

    def open_emoji_menu(self):
        emoji_window = tk.Toplevel(self.master)
        emoji_window.title(self.get_text('emoji'))  # "Select Emoji" translated

        # 一些示例表情
        emojis = ["😊", "😂", "😍", "😢", "😡", "👍", "🎉"]

        for emoji in emojis:
            button = ttk.Button(emoji_window, text=emoji, command=lambda e=emoji: self.insert_emoji(e))
            button.pack(side=tk.LEFT, padx=5)

    def insert_emoji(self, emoji):
        current_text = self.entry.get()
        self.entry.delete(0, tk.END)
        self.entry.insert(0, current_text + emoji)

    def show_program_info(self):
        program_info = (
            "程序名称: 聊天客户端\n"  # "Program Name: Chat Client" translated
            "版本: Release_0.0.1_V1\n"  # "Version: 1.0.0" translated
            "作者: (GitHub) Buelie\n"  # "Author: (GitHub) Buelie" translated"
            "作者: (Bilibili) 腾海QWQ\n"  # "Author: (Bilibili) 腾海QWQ" translated"
            "作者: (QQ) 账号已封禁&陆御\n"  # "Author: (QQ) 账号已封禁&陆御" translated"
            "作者: (中国) 罗*琳\n"  # "Author: (China) 罗*琳" translated"
            "描述: 一个简单的聊天客户端应用程序。\n"  # "Description: A simple chat client application." translated
            "用法: 连接到服务器，发送消息，发送文件，等等。"  # "Usage: Connect to a server, send messages, send files, and more." translated
        )
        messagebox.showinfo(self.get_text('program_info_title'), program_info)

    def get_text(self, key):
        translations = {
            'send': {
                'en': 'Send',
                'zh': '发送',
                'ru': 'Отправить',
                'fr': 'Envoyer',
                'es': 'Enviar',
                'de': 'Senden',
                'ja': '送信',
                'ko': '전송'
            },
            'send_file': {
                'en': 'Send File',
                'zh': '发送文件',
                'ru': 'Отправить файл',
                'fr': 'Envoyer un fichier',
                'es': 'Enviar archivo',
                'de': 'Datei senden',
                'ja': 'ファイル送信',
                'ko': '파일 전송'
            },
            'send_file_to_user': {
                'en': 'Send File to User',
                'zh': '发送文件给用户',
                'ru': 'Отправить файл пользователю',
                'fr': 'Envoyer un fichier à l\'utilisateur',
                'es': 'Enviar archivo al usuario',
                'de': 'Datei an Benutzer senden',
                'ja': 'ユーザーにファイルを送信',
                'ko': '사용자에게 파일 전송'
            },
            'send_private': {
                'en': 'Send Private',
                'zh': '发送私信',
                'ru': 'Отправить личное сообщение',
                'fr': 'Envoyer Privé',
                'es': 'Enviar Privado',
                'de': 'Privat senden',
                'ja': 'プライベート送信',
                'ko': '비공식 전송'
            },
            'private_message': {
                'en': 'Private Message',
                'zh': '私信',
                'ru': 'Личное сообщение',
                'fr': 'Message privé',
                'es': 'Mensaje privado',
                'de': 'Private Nachricht',
                'ja': 'プライベートメッセージ',
                'ko': '비공식 메시지'
            },
            'private_nickname': {
                'en': 'Nickname:',
                'zh': '昵称:',
                'ru': 'Псевдоним:',
                'fr': 'Surnom:',
                'es': 'Apodo:',
                'de': 'Spitzname:',
                'ja': 'ニックネーム:',
                'ko': '닉네임:'
            },
            'server': {
                'en': 'Server',
                'zh': '服务器',
                'ru': 'Сервер',
                'fr': 'Serveur',
                'es': 'Servidor',
                'de': 'Server',
                'ja': 'サーバー',
                'ko': '서버'
            },
            'you': {
                'en': 'You',
                'zh': '你',
                'ru': 'Вы',
                'fr': 'Vous',
                'es': 'Tú',
                'de': 'Du',
                'ja': 'あなた',
                'ko': '당신'
            },
            'connection': {
                'en': 'Connection',
                'zh': '连接',
                'ru': 'Соединение',
                'fr': 'Connexion',
                'es': 'Conexión',
                'de': 'Verbindung',
                'ja': '接続',
                'ko': '연결'
            },
            'nickname': {
                'en': 'Nickname:',
                'zh': '昵称:',
                'ru': 'Псевдоним:',
                'fr': 'Surnom:',
                'es': 'Apodo:',
                'de': 'Spitzname:',
                'ja': 'ニックネーム:',
                'ko': '닉네임:'
            },
            'server_address': {
                'en': 'Server Address:',
                'zh': '服务器地址:',
                'ru': 'Адрес сервера:',
                'fr': 'Adresse du serveur:',
                'es': 'Dirección del servidor:',
                'de': 'Serveradresse:',
                'ja': 'サーバーアドレス:',
                'ko': '서버 주소:'
            },
            'port': {
                'en': 'Port:',
                'zh': '端口:',
                'ru': 'Порт:',
                'fr': 'Port:',
                'es': 'Puerto:',
                'de': 'Port:',
                'ja': 'ポート:',
                'ko': '포트:'
            },
            'connect': {
                'en': 'Connect',
                'zh': '连接',
                'ru': 'Подключить',
                'fr': 'Connecter',
                'es': 'Conectar',
                'de': 'Verbinden',
                'ja': '接続',
                'ko': '연결'
            },
            'chat_area': {
                'en': 'Chat Area',
                'zh': '聊天区域',
                'ru': 'Чат',
                'fr': 'Zone de chat',
                'es': 'Área de chat',
                'de': 'Chat-Bereich',
                'ja': 'チャットエリア',
                'ko': '채팅 영역'
            },
            'connected_message': {
                'en': 'Connected to the server!',
                'zh': '已连接到服务器！',
                'ru': 'Подключено к серверу!',
                'fr': 'Connecté au serveur!',
                'es': '¡Conectado al servidor!',
                'de': 'Mit dem Server verbunden!',
                'ja': 'サーバーに接続されました！',
                'ko': '서버에 연결되었습니다!'
            },
            'port_error': {
                'en': 'Invalid port number.',
                'zh': '无效的端口号。',
                'ru': 'Неверный номер порта.',
                'fr': 'Numéro de port invalide.',
                'es': 'Número de puerto no válido.',
                'de': 'Ungültige Portnummer.',
                'ja': '無効なポート番号。',
                'ko': '잘못된 포트 번호입니다.'
            },
            'connection_error': {
                'en': 'Connection error',
                'zh': '连接错误',
                'ru': 'Ошибка соединения',
                'fr': 'Erreur de connexion',
                'es': 'Error de conexión',
                'de': 'Verbindungsfehler',
                'ja': '接続エラー',
                'ko': '연결 오류'
            },
            'nickname_warning': {
                'en': 'Please enter a nickname.',
                'zh': '请输入昵称。',
                'ru': 'Пожалуйста, введите псевдоним.',
                'fr': 'Veuillez entrer un surnom.',
                'es': 'Por favor, introduce un apodo.',
                'de': 'Bitte einen Spitznamen eingeben.',
                'ja': 'ニックネームを入力してください。',
                'ko': '닉네임을 입력해 주세요.'
            },
            'not_connected_warning': {
                'en': 'You are not connected to the server.',
                'zh': '您未连接到服务器。',
                'ru': 'Вы не подключены к серверу.',
                'fr': 'Vous n’êtes pas connecté au serveur.',
                'es': 'No estás conectado al servidor.',
                'de': 'Sie sind nicht mit dem Server verbunden.',
                'ja': 'サーバーに接続されていません。',
                'ko': '서버에 연결되지 않았습니다.'
            },
            'error_receiving': {
                'en': 'Error receiving message',
                'zh': '接收消息出错',
                'ru': 'Ошибка получения сообщения',
                'fr': 'Erreur lors de la réception du сообщения',
                'es': 'Error al recibir el mensaje',
                'de': 'Fehler beim Empfang der Nachricht',
                'ja': 'メッセージの受信エラー',
                'ko': '메시지 수신 오류'
            },
            'reply': {
                'en': 'Reply',
                'zh': '回复',
                'ru': 'Ответить',
                'fr': 'Répondre',
                'es': 'Responder',
                'de': 'Antworten',
                'ja': '返信',
                'ko': '답장'
            },
            'recall': {
                'en': 'Recall',
                'zh': '撤回',
                'ru': 'Отозвать',
                'fr': 'Révoquer',
                'es': 'Revocar',
                'de': 'Widerrufen',
                'ja': '取り消す',
                'ko': '취소'
            },
            'status_connected': {
                'en': 'Status: Connected',
                'zh': '状态：已连接',
                'ru': 'Статус: Подключено',
                'fr': 'Statut: Connecté',
                'es': 'Estado: Conectado',
                'de': 'Status: Verbunden',
                'ja': 'ステータス: 接続済み',
                'ko': '상태: 연결됨'
            },
            'status_disconnected': {
                'en': 'Status: Disconnected',
                'zh': '状态：未连接',
                'ru': 'Статус: Отключено',
                'fr': 'Statut: Déconnecté',
                'es': 'Estado: Desconectado',
                'de': 'Status: Getrennt',
                'ja': 'ステータス: 切断',
                'ko': '상태: 연결 끊김'
            },
            'warning': {
                'en': 'Warning',
                'zh': '警告',
                'ru': 'Предупреждение',
                'fr': 'Avertissement',
                'es': 'Advertencia',
                'de': 'Warnung',
                'ja': '警告',
                'ko': '경고'
            },
            'error': {
                'en': 'Error',
                'zh': '错误',
                'ru': 'Ошибка',
                'fr': 'Erreur',
                'es': 'Error',
                'de': 'Fehler',
                'ja': 'エラー',
                'ko': '오류'
            },
            'file_sent': {
                'en': 'File sent successfully!',
                'zh': '文件发送成功！',
                'ru': 'Файл успешно отправлен!',
                'fr': 'Fichier envoyé avec succès!',
                'es': '¡Archivo enviado con éxito!',
                'de': 'Datei erfolgreich gesendet!',
                'ja': 'ファイルが正常に送信されました！',
                'ko': '파일이 성공적으로 전송되었습니다!'
            },
            'file_received': {
                'en': 'File received: ',
                'zh': '接收到文件：',
                'ru': 'Файл получен: ',
                'fr': 'Fichier reçu: ',
                'es': 'Archivo recibido: ',
                'de': 'Datei empfangen: ',
                'ja': '受信したファイル: ',
                'ko': '받은 파일: '
            },
            'file_error': {
                'en': 'Error sending file.',
                'zh': '发送文件出错。',
                'ru': 'Ошибка при отправке файла.',
                'fr': 'Erreur lors de l\'envoi du файла.',
                'es': 'Error al enviar el archivo.',
                'de': 'Fehler beim Senden der Datei.',
                'ja': 'ファイル送信中にエラーが発生しました。',
                'ko': '파일 전송 중 오류가 발생했습니다.'
            },
            'export_chat': {
                'en': 'Export Chat',
                'zh': '导出聊天记录',
                'ru': 'Экспорт чата',
                'fr': 'Exporter le chat',
                'es': 'Exportar chat',
                'de': 'Chat exportieren',
                'ja': 'チャットをエクスポート',
                'ko': '채팅 내보내기'
            },
            'program_info': {
                'en': 'Program Info',
                'zh': '程序信息',
                'ru': 'Информация о программе',
                'fr': 'Informations sur le programme',
                'es': 'Información del programa',
                'de': 'Programminformationen',
                'ja': 'プログラム情報',
                'ko': '프로그램 정보'
            },
            'program_info_title': {
                'en': 'Program Information',
                'zh': '程序信息',
                'ru': 'Информация о программе',
                'fr': 'Informations sur le programme',
                'es': 'Información del programa',
                'de': 'Programminformationen',
                'ja': 'プログラム情報',
                'ko': '프로그램 정보'
            },
            'emoji': {
                'en': 'Select an emoji',
                'zh': '选择表情',
                'ru': 'Выберите смайлик',
                'fr': 'Sélectionner une émoticône',
                'es': 'Selecciona un emoticono',
                'de': 'Wähle ein Emote aus',
                'ja': 'スタンプを選択する',
                'ko': '이모티콘 선택',
            },
            'please_enter_private_message': {
                'en': 'Please enter a private message.',
                'zh': '请输入私信内容。',
                'ru': 'Пожалуйста, введите личное сообщение.',
                'fr': 'Veuillez entrer un message privé.',
                'es': 'Por favor, introduce un mensaje privado.',
                'de': 'Bitte geben Sie eine private Nachricht ein.',
                'ja': 'プライベートメッセージを入力してください。',
                'ko': '비공식 메시지를 입력해 주세요.'
            },
            'chat_exported': {
                'en': 'Chat history exported successfully!',
                'zh': '聊天记录导出成功！',
                'ru': 'История чата успешно экспортирована!',
                'fr': 'Historique de discussion exporté avec succès!',
                'es': '¡Historial de chat exportado con éxito!',
                'de': 'Chatverlauf erfolgreich exportiert!',
                'ja': 'チャット履歴が正常にエクスポートされました！',
                'ko': '채팅 기록이 성공적으로 내보내졌습니다!'
            },
            'query_user_id': {
                'en': 'Query User ID',
                'zh': '查询用户ID',
                'ru': 'Запросить ID пользователя',
                'fr': 'Demander l\'ID utilisateur',
                'es': 'Consultar ID de usuario',
                'de': 'Benutzer-ID abfragen',
                'ja': 'ユーザーIDを照会',
                'ko': '사용자 ID 조회'
            },
        }
        return translations[key].get(self.language)

    def change_language(self, event):
        selected_language = self.language_menu.get()
        self.language = 'zh' if selected_language == "中文" else 'ru' if selected_language == "Русский" else 'fr' if selected_language == "Français" else 'es' if selected_language == "Español" else 'de' if selected_language == "Deutsch" else 'ja' if selected_language == "日本語" else 'ko' if selected_language == "한국어" else 'en'
        self.update_texts()

    def update_texts(self):
        self.info_button.config(text=self.get_text('program_info'))
        self.nickname_label.config(text=self.get_text('nickname'))
        self.address_label.config(text=self.get_text('server_address'))
        self.port_label.config(text=self.get_text('port'))
        self.connect_button.config(text=self.get_text('connect'))
        self.chat_frame.config(text=self.get_text('chat_area'))
        self.send_button.config(text=self.get_text('send'))
        self.file_button.config(text=self.get_text('send_file'))
        self.send_file_to_user_button.config(text=self.get_text('send_file_to_user'))  # 更新发送文件按钮
        self.reply_button.config(text=self.get_text('reply'))
        self.recall_button.config(text=self.get_text('recall'))
        self.private_message_frame.config(text=self.get_text('private_message'))
        self.private_nickname_label.config(text=self.get_text('private_nickname'))
        self.send_private_button.config(text=self.get_text('send_private'))
        self.export_button.config(text=self.get_text('export_chat'))  # 更新导出按钮文本
        self.status_label.config(text=self.get_text('status_disconnected'), foreground='red')  # 初始状态为未连接
        self.query_nickname_label.config(text=self.get_text('nickname'))  # 更新查询标签
        self.query_user_id_button.config(text=self.get_text('query_user_id'))  # 更新查询按钮文本

    def generate_user_id(self):
        return str(uuid.uuid4())

    def connect_to_server(self):
        self.nickname = self.nickname_entry.get().strip()
        if not self.nickname:
            messagebox.showwarning("Warning", self.get_text('nickname_warning'))
            return

        # 生成用户唯一ID
        self.user_id = self.generate_user_id()

        address = self.address_entry.get()
        port = self.port_entry.get()

        try:
            port = int(port)
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((address, port))

            self.text_area.configure(state='normal')
            self.text_area.insert(tk.END, self.get_text('connected_message') + "\n")
            self.text_area.configure(state='disabled')

            self.connect_button.config(state='disabled')
            self.is_connected = True
            self.status_label.config(text=self.get_text('status_connected'), foreground='green')

            # 更新用户ID标签
            self.user_id_label.config(text=f"User ID: {self.user_id}")

            self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receive_thread.start()

        except ValueError:
            messagebox.showerror("Error", self.get_text('port_error'))
        except Exception as e:
            messagebox.showerror("Error", f"{self.get_text('connection_error')}: {e}")

    def query_user_id(self):
        if not self.client_socket:
            messagebox.showwarning("Warning", self.get_text('not_connected_warning'))
            return

        nickname_to_query = self.query_nickname_entry.get().strip()
        if nickname_to_query:
            # 发送查询请求给服务器
            query_message = f"QUERY_ID:{nickname_to_query}"
            self.client_socket.send(query_message.encode('utf-8'))
        else:
            messagebox.showwarning("Warning", self.get_text('please_enter_private_message'))

    def save_chat_history(self):
        with open("chat_history.txt", "a", encoding='utf-8') as f:
            for message in self.sent_messages:
                f.write(message + "\n")

    def export_chat_history(self):
        """导出聊天记录到文件"""
        chat_history_file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if chat_history_file:
            with open(chat_history_file, "w", encoding='utf-8') as file:
                for message in self.sent_messages:
                    file.write(message + "\n")
            messagebox.showinfo("Success", self.get_text('chat_exported'))

    def send_message(self):
        if not self.client_socket:
            messagebox.showwarning("Warning", self.get_text('not_connected_warning'))
            return

        message = self.entry.get()
        if message:
            full_message = f"{self.user_id}:{self.nickname}: {message}"  # 添加用户ID到消息中
            self.client_socket.send(full_message.encode('utf-8'))
            self.sent_messages.append(full_message)  # 保存发送的消息
            self.entry.delete(0, tk.END)

            self.text_area.configure(state='normal')
            self.text_area.insert(tk.END, f"{self.get_text('you')}: {message}\n")
            self.text_area.configure(state='disabled')

            self.save_chat_history()  # 保存聊天记录

    def send_private_message(self):
        if not self.client_socket:
            messagebox.showwarning("Warning", self.get_text('not_connected_warning'))
            return

        recipient_nickname = self.private_nickname_entry.get().strip()
        message = self.private_message_entry.get().strip()
        if recipient_nickname and message:
            full_message = f"@{recipient_nickname}:{self.user_id}:{self.nickname}: {message}"
            self.client_socket.send(full_message.encode('utf-8'))
            self.private_message_entry.delete(0, tk.END)  # 清空输入框

            self.text_area.configure(state='normal')
            self.text_area.insert(tk.END, f"{self.get_text('you')} -> {recipient_nickname}: {message}\n")
            self.text_area.configure(state='disabled')
        else:
            messagebox.showwarning("Warning", self.get_text('please_enter_private_message'))

    def send_file(self):
        if not self.client_socket:
            messagebox.showwarning("Warning", self.get_text('not_connected_warning'))
            return

        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                with open(file_path, 'rb') as file:
                    self.client_socket.sendall(file.read())
                self.text_area.configure(state='normal')
                self.text_area.insert(tk.END, self.get_text('file_sent') + "\n")
                self.text_area.configure(state='disabled')
            except Exception as e:
                messagebox.showerror("Error", self.get_text('file_error'))

    def send_file_to_user(self):
        if not self.client_socket:
            messagebox.showwarning("Warning", self.get_text('not_connected_warning'))
            return

        recipient_nickname = self.private_nickname_entry.get().strip()
        if recipient_nickname:
            file_path = filedialog.askopenfilename()
            if file_path:
                try:
                    with open(file_path, 'rb') as file:
                        file_data = file.read()
                        full_message = f"FILE_TO:{recipient_nickname}:{self.user_id}:{self.nickname}:" + file_data.decode('latin-1')  # 将二进制数据编码为字符串
                        self.client_socket.send(full_message.encode('utf-8'))
                    self.text_area.configure(state='normal')
                    self.text_area.insert(tk.END, f"{self.get_text('you')} -> {recipient_nickname}: File sent successfully!\n")
                    self.text_area.configure(state='disabled')
                except Exception as e:
                    messagebox.showerror("Error", self.get_text('file_error'))
        else:
            messagebox.showwarning("Warning", "Please specify the recipient's nickname.")

    def reply_to_last_message(self):
        if self.sent_messages:
            last_message = self.sent_messages[-1]
            self.entry.delete(0, tk.END)
            self.entry.insert(0, f"Replying to: {last_message}")

    def recall_last_message(self):
        if self.sent_messages:
            last_message = self.sent_messages.pop()  # 移除最后一条消息
            self.text_area.configure(state='normal')
            self.text_area.insert(tk.END, f"{self.get_text('you')}: (message recalled)\n")
            self.text_area.configure(state='disabled')

            # 通知服务器撤回消息
            recall_message = f"{self.nickname} has recalled a message."
            self.client_socket.send(recall_message.encode('utf-8'))

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message:
                    parts = message.split(':', 2)
                    if len(parts) == 3:
                        user_id, nickname, msg = parts
                        self.text_area.configure(state='normal')
                        self.text_area.insert(tk.END, f"{nickname} (ID: {user_id}): {msg}\n")  # 显示用户昵称和ID
                        self.text_area.configure(state='disabled')
                    elif message.startswith("USER_ID:"):
                        # 处理查询返回的用户ID
                        nickname, user_id = message.split(':')[1:3]
                        messagebox.showinfo("User ID", self.get_text('user_id_query').format(nickname, user_id))  # 弹窗显示用户ID
                    elif message.startswith("FILE_TO:"):
                        # 处理文件接收逻辑
                        parts = message.split(':', 4)
                        recipient_nickname, sender_user_id, sender_nickname, file_data = parts[1], parts[2], parts[3], parts[4]
                        with open(f"received_file_from_{sender_nickname}.dat", "wb") as f:
                            f.write(file_data.encode('latin-1'))  # 将字符串解码为字节并保存
                        self.text_area.configure(state='normal')
                        self.text_area.insert(tk.END, f"Received file from {sender_nickname}.\n")
                        self.text_area.configure(state='disabled')
                else:
                    break
            except Exception as e:
                self.text_area.configure(state='normal')
                self.text_area.insert(tk.END, f"{self.get_text('error_receiving')}: {e}\n")
                self.text_area.configure(state='disabled')
                break

        self.client_socket.close()
        self.is_connected = False
        self.status_label.config(text=self.get_text('status_disconnected'), foreground='red')

if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
