import socket
import traceback

import select
import time

from PyQt5.QtCore import QThread

HOST = '118.37.147.48'
PORT = 5000

class socket_server_thread(QThread):
    def __init__(self):
        super().__init__()
        self.socks = []
        self.con = False

    def send_all(self, data):
        try:
            if self.con :
                for i in self.socks:
                    if i != self.s:#본인을 제외한 모든 소켓에 송신
                        #print(i)
                        print("메세지 송신",data)
                        i.sendall(data.encode('utf-8'))
            else:
                print("연결되지 않음 메세지 전송 실패")
        except:
            #중요정보 로그 !!
            pass

    def run(self):
        while self.con == False:
            try:
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
                                else:  # 이미 접속한 클라이언트의 요청
                                    try:
                                        conn = sock
                                        data = conn.recv(1024).decode('utf-8')
                                        print(f'데이터 수신 : {data}')

                                    except ConnectionResetError:
                                        print("클라이언트 접속 해제 : 연결 삭제")
                                        #print(ConnectionResetError)
                                        sock.close()
                                        self.socks.remove(sock)
                                    except Exception as e:
                                        print(traceback.format_exc())
                                        print(e)
                                        pass
                                        #중요정보 로그 !!
                        except:
                            print(traceback.format_exc())
            except:
                print("asd")


a = socket_server_thread()
a.start()

while True:
    time.sleep(15)
    a.send_all("BUY;005930;1") #미보유
    time.sleep(1)
    a.send_all("BUY;005930;2") #미보유
    time.sleep(1)
    a.send_all("BUY;005930;3") #미보유
    time.sleep(1)
    a.send_all("BUY;005930;4") #미보유
    time.sleep(1)
    a.send_all("SEL;005930;1")  # 미보유
    time.sleep(1)
    a.send_all("SEL;005930;2")  # 미보유
    time.sleep(1)
    a.send_all("SEL;005930;3")  # 미보유
    time.sleep(1)
    a.send_all("SEL;005930;4")  # 미보유
    time.sleep(1)


    a.send_all("SEL;005030;1")
    time.sleep(1)
    a.send_all("SEL;005030;2")
    time.sleep(1)
    a.send_all("SEL;005030;3")
    time.sleep(1)
    a.send_all("SEL;005030;4")
    time.sleep(1)

    a.send_all("BUY;005030;1")
    time.sleep(1)
    a.send_all("BUY;005030;2")
    time.sleep(1)
    a.send_all("BUY;005030;3")
    time.sleep(1)
    a.send_all("BUY;005030;4")
    time.sleep(1)
