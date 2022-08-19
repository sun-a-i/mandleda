import socket

HOST = '192.168.0.7'
PORT = 50007

msg = "보낼 메세지"

class client():

    def run(self):
        global msg
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            while True:
                if msg != '':
                    s.sendall(msg.encode('utf-8'))
                    msg = ''

                data = s.recv(1024).decode('utf-8')
                print(f'서버응답:{data}')


a = client()
a.run()