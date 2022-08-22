import socket
import traceback

import select
import time

from PyQt5.QtCore import QThread

HOST = '218.155.43.223'
PORT = 5000

class sock_server_run(QThread):
    def __init__(self):
        super().__init__()
        self.socks = []
        self.con = False

    def send_all(self, data):
        for i in self.socks:
            if i != self.s:#본인을 제외한 모든 소켓에 송신
                print(i)
                print("메세지 송신")
                i.sendall(data.encode('utf-8'))

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.s:
            #s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((HOST, PORT))
            self.s.listen()
            self.con = True
            print('서버가 시작되었습니다.')
            self.socks = [self.s]
            while True:
                try:
                    self.readables, self.writeables, self.excpetions = select.select(self.socks, [], []) # 이벤트 대기 ex)클라이언트 접속, 리시브
                    for sock in self.readables:
                        if sock == self.s:  # 신규 클라이언트 접속
                            newsock, addr = self.s.accept()
                            self.socks.append(newsock)
                            print("새로운 클라이언트 접속")
                        else:
                            try:
                                data = sock.recv(1024).decode('utf-8')

                                print(f'데이터 수신 : {data}')

                            except ConnectionResetError :
                                print("연결 오류 : 연결 삭제")
                                sock.close()
                                self.socks.remove(sock)
                except:
                    print(traceback.format_exc())

                       # conn = sock
                        #data = conn.recv(1024).decode('utf-8')
                        #if data:
                        #    print(f'데이터 수신 : {data}')
                        #else:
                          #  print("데이터 없음 ?")


a = sock_server_run()
a.start()

while True:
    pass
