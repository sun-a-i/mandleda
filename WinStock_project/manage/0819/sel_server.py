import socket
import select
import time

HOST = '192.168.0.7'
PORT = 50007

class sock_server_run():
    def __init__(self):
        self.socks = []

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
            print('서버가 시작되었습니다.')
            self.socks = [self.s]
            while True:
                self.readables, self.writeables, self.excpetions = select.select(self.socks, [], []) # 이벤트 대기 ex)클라이언트 접속, 리시브
                for sock in self.readables:
                    if sock == self.s:  # 신규 클라이언트 접속
                        newsock, addr = self.s.accept()
                        self.socks.append(newsock)
                        print("새로운 클라이언트 접속")
                    else:  # 이미 접속한 클라이언트의 요청
                        conn = sock
                        data = conn.recv(1024).decode('utf-8')
                        print(f'데이터 수신 : {data}')

a = sock_server_run()
a.run()

