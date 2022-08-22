import time
import traceback

from PyQt5.QtCore import QThread

import socket

HOST = '218.155.43.223'
PORT = 5000

class socket_thread(QThread):
    def __init__(self):
        super().__init__()
        self.con = False

    def run(self):
        while self.con == False:
            try:
                time.sleep(3)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.s:
                    self.s.connect((HOST, PORT))
                    self.con = True
                    while True:
                        data = self.s.recv(1024).decode('utf-8')
                        print(f'서버응답:{data}')
            except:
                self.con = False
                print("서버 접속 불가")


    def send_msg(self, msg):
        if self.con :
            self.s.sendall(msg.encode('utf-8'))
        else:
            print("서버 접속 불가, 메세지 전송되지 않음")


a = socket_thread()
a.start()

while True:
    time.sleep(5)
    a.send_msg("메세지 보냅니다2")
