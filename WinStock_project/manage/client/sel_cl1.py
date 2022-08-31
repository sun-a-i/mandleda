import time
import traceback

from PyQt5.QtCore import QThread

import socket

HOST = '192.168.0.7'
PORT = 5050

class socket_client_thread(QThread):
    def __init__(self):
        super().__init__()
        self.con = False

    def send_msg(self, msg):
        try:
            if self.con :
                self.s.sendall(msg.encode('utf-8'))
            else:
                print("서버 접속 불가, 메세지 전송되지 않음")
        except:
            pass

    def run(self):
        while True:
            try:
                time.sleep(3)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.s:
                    self.s.connect((HOST, PORT))
                    self.con = True
                    while True:
                        data = self.s.recv(1024).decode('utf-8')
                        print(f'서버응답:{data}')
            except Exception as e:
                self.con = False
                print(e)
                #print(traceback.format_exc())
                print("서버 접속 불가")





a = socket_client_thread()
a.start()

while True:
    pass
