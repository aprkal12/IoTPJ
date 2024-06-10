import socket
import threading
from datetime import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("iotpj-b5968-firebase-adminsdk-ito8f-7eceec2f32.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

collection_name = 'sensor_data'
document_name = 'mq137'

dict_msg = {}
dict_msg['fan'] = 0
dict_msg['sprayCount'] = 0

class TestAgent:
    port = 10020
    sendcount = 0
    

    def __init__(self):
        print("TestAgent Initialized.")
        global dict_msg

    def agent_start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        print("TestAgent Started")
        count = 0
        try:
            while True:
                count += 1
                client_socket, addr = self.server_socket.accept()
                print("Connection Requested.")
                TestAgentReceiveThread(client_socket).start()
                if count == 200:
                    print("Data is saved to Firestore")
                    doc_ref = db.collection(collection_name).document(document_name)
                    doc_ref.set(dict_msg)
                    count = 0
        except Exception as e:
            print(str(e))

class TestAgentReceiveThread(threading.Thread):
    def __init__(self, client_socket):
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        # self.msg_list = msg_list
        global dict_msg

    def get_server_info(self):
        ip = socket.gethostbyname(socket.gethostname())
        msg = f"{ip}:{TestAgent.port}"
        return msg

    def get_time(self):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return now

    def get_send_count(self):
        msg = str(TestAgent.sendcount)
        return msg

    def send_message(self, msg):
        self.client_socket.sendall((msg + "\n").encode())
        print("Sent:", msg)
        TestAgent.sendcount += 1

    def run(self):
        try:
            while True:
                receivedmsg = self.client_socket.recv(1024).decode().strip()
                if receivedmsg:
                    print(">", receivedmsg)

                    if receivedmsg == "[disconnect]":
                        break
                    elif receivedmsg == "[info]":
                        sendmsg = self.get_server_info()
                    elif receivedmsg == "[time]":
                        sendmsg = self.get_time()
                    elif receivedmsg == "[count]":
                        sendmsg = self.get_send_count()
                    else:
                        parts = receivedmsg.split(",")
                        gas_part = parts[0].split(":")[1].strip().split(" ")[0]
                        elec_part = parts[1].strip().split(" ")[0]
                        gas = float(gas_part)
                        elec = float(elec_part)

                        dict_msg['gas'] = gas
                        dict_msg['elec'] = elec


                        # 수정 필요 fan_flag 는 스레드 실행하면 매번 초기화 됨
                        if gas < 10.0 and dict_msg['fan'] == 1: # 가스수치가 기준치 아래로 돌아오고 환풍기가 켜져있는 상태
                            dict_msg['fan'] = 0
                            sendmsg = "2"
                        elif gas >= 10.0 and dict_msg['fan'] == 0: # 가스수치가 기준치 초과되고 환풍기가 꺼져있는 상태
                            dict_msg['fan'] = 1
                            dict_msg['sprayCount'] += 1
                            sendmsg = "1"    
                        elif gas >= 10.0 and dict_msg['fan'] == 1: # 가스수치가 기준치 초과되고 환풍기가 켜져있는 상태
                            sendmsg = "0"
                        else:
                            sendmsg = "0"


                    self.send_message(sendmsg)
            print("Client is disconnected.")
            self.client_socket.close()
        except Exception as e:
            print("catch")
            print(str(e))

if __name__ == "__main__":
    ta = TestAgent()
    ta.agent_start()
