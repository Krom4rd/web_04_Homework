from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, unquote_plus
from threading import Thread
from datetime import datetime
import socket
from pathlib import Path
import mimetypes
import json

HTTP_HOST = "0.0.0.0"
HTTP_PORT = 3000
SOCKET_HOST = "0.0.0.0"
SOCKET_PORT = 5000

class HttpGetHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # print(f"{self.headers.get('content-Length')}")
        data =self.rfile.read(int(self.headers.get('content-Length')))
        self.save_to_json(data)
        # print(f"{data = }")
        # print(f"{unquote_plus(data.decode()) = }")
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        match url.path:
            case '/':
                self.send_html('index.html')
            case '/send_massage':
                self.send_html('send_message.html')
            case _:
                # print(url.path[1:])
                # print(f"{file_path.exists() = }")
                file_path = Path(url.path[1:])
                if file_path.exists():
                    self.send_static(str(file_path))
                else:
                    self.send_html('error.html', 404)

    def send_static(self, static_filename):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        self.send_header('content-type', mt[0])
        self.end_headers()
        with open(static_filename, 'rb') as file:
            self.wfile.write(file.read())

    def send_html(self, html_filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(html_filename, 'rb') as file:
            self.wfile.write(file.read())

    def save_to_json(self, raw_data):
        data = unquote_plus(raw_data.decode())
        dict_data = {str(datetime.now()):{key: value for key, value in [el.split("=") for el in data.split("&")]}}
        # Формат словника для запису в json файл {час: {"username": ...., "message": ....}}
        # print(dict_data)
        if not Path("storage/data.json").exists():
            with open("storage/data.json", "w", encoding="utf-8") as file:
                json.dump(dict_data, file)
        else:
            data_json_file = {}
            with open("storage/data.json",'r',encoding='utf-8') as file:
                try:
                    data_json_file = json.load(file)
                except json.decoder.JSONDecodeError: # Обробка помилки яка виникає якщо файл пустий
                    pass
            data_json_file.update(dict_data)
            with open("storage/data.json", "w", encoding="utf-8") as file:
                json.dump(data_json_file, file)

def socket_server(host, port):
    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen(10)
    conn, address = server_socket.accept()
    print(f'Connection from {address}')
    while True:
        data = conn.recv(100).decode()

        if not data:
            break
        print(f'received message: {data}')
        massage_for_save = {str(datetime.now()):{'username':address, 'massage': data}}
        if not Path("storage/data.json").exists():
            with open("storage/data.json", "w", encoding="utf-8") as file:
                json.dump(massage_for_save, file)
        else:
            data_json_file = {}
            with open("storage/data.json",'r',encoding='utf-8') as file:
                try:
                    data_json_file = json.load(file)
                except json.decoder.JSONDecodeError: # Обробка помилки яка виникає якщо файл пустий
                    pass
            data_json_file.update(massage_for_save)
            with open("storage/data.json", "w", encoding="utf-8") as file:
                json.dump(data_json_file, file)
        message = input('--> ')
        conn.send(message.encode())
    conn.close()

def client():
    host = socket.gethostname()
    port = 5000

    client_socket = socket.socket()
    client_socket.connect((host, port))
    message = input('--> ')

    while message.lower().strip() != 'end':
        client_socket.send(message.encode())
        data = client_socket.recv(1024).decode()
        print(f'received message: {data}')
        message = input('--> ')

    client_socket.close()

def run(host, port):
    server_address = (host, port)
    # print(server_address)
    http = HTTPServer(server_address, HttpGetHandler)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

def main():
    server_run = Thread(target=run, args=(HTTP_HOST, HTTP_PORT))
    server_run.start()

    socket_server_run = Thread(target=socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    socket_server_run.start()

    while True:
        if  not socket_server_run.is_alive():
            socket_server_run = Thread(target=socket_server, args=(SOCKET_HOST, SOCKET_PORT))
            socket_server_run.start()

if __name__ == "__main__":
    main()