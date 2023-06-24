import socket
import json
import os
import base64


TARGET_IP = "localhost"
TARGET_PORT = 55555

class ChatClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (TARGET_IP,TARGET_PORT)
        self.sock.connect(self.server_address)
        self.tokenid=""
        self.direktori_save = './'  # Specify the directory to save received files

    def proses(self,cmdline):
        j=cmdline.split(" ")
        try:
            command=j[0].strip()
            if (command=='auth'):
                username=j[1].strip()
                password=j[2].strip()
                return self.login(username,password)
            
            elif (command=='sendfile'):
                usernameto = j[1].strip()
                filepath = j[2].strip()
                return self.send_file(usernameto,filepath)
            
            elif (command=='addrealmconnect'):
                realm_ID = j[1].strip()
                realm_address = j[2].strip()
                realm_port = j[3].strip()
                return self.add_realm_connect(realm_ID, realm_address, realm_port)
            
            elif (command=='send'):
                usernameto = j[1].strip()
                message=""
                for w in j[2:]:
                    message="{} {}" . format(message,w)
                return self.send_message(usernameto,message)
            
            elif (command=='sendgroup'):
                group_usernames = j[1].strip()
                message=""
                for w in j[2:]:
                    message="{} {}" . format(message,w)
                return self.send_group_message(group_usernames,message)
            
            elif (command == 'sendrealm'):
                realm_ID = j[1].strip()
                username_to = j[2].strip()
                message = ""
                for w in j[3:]:
                    message = "{} {}".format(message, w)
                return self.send_realm_message(realm_ID, username_to, message)
            
            elif (command=='sendrealmgroup'):
                realm_ID = j[1].strip()
                group_usernames = j[2].strip()
                message=""
                for w in j[3:]:
                    message="{} {}" . format(message,w)
                return self.send_group_realm_message(realm_ID, group_usernames,message)
            
            elif (command=='inbox'):
                return self.inbox()
            
            elif (command == 'inboxrealm'):
                realm_ID = j[1].strip()
                return self.inbox_realm(realm_ID)
            else:
                return "*Sorry, Incorrect command"
        except IndexError:
            return "-Sorry, Incorrect command"

    def sendstring(self,string):
        try:
            self.sock.sendall(string.encode())
            receivemsg = ""
            while True:
                data = self.sock.recv(64)
                print("diterima dari server",data)
                if (data):
                    receivemsg = "{}{}" . format(receivemsg,data.decode())  #data harus didecode agar dapat di operasikan dalam bentuk string
                    if receivemsg[-4:]=='\r\n\r\n':
                        print("end of string")
                        return json.loads(receivemsg)
        except:
            self.sock.close()
            return { 'status' : 'ERROR', 'message' : 'Failed'}
        
    def send_file(self, usernameto="xxx", filepath="xxx"):
        if (self.tokenid==""):
            return "Error, not authorized"

        if not os.path.exists(filepath):
            return {'status': 'ERROR', 'message': 'File not found'}
        
        with open(filepath, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content)  
        string="sendfile {} {} {} {}\r\n" . format(self.tokenid,usernameto,filepath,encoded_content)

        result = self.sendstring(string)
        if result['status']=='OK':
            return "file sent to {}" . format(usernameto)
        else:
            return "Error, {}" . format(result['message'])

    def login(self,username,password):
        command = f"auth {username} {password} \r\n"
        response = self.sendstring(command)
        if response['status']=='OK':
            self.tokenid=response['tokenid']
            return "username {} logged in, token {} " .format(username,self.tokenid)
        else:
            return "Error, {}" . format(response['message'])

    def send_message(self,usernameto="xxx",message="xxx"):
        if not self.tokenid:
            return "Error, Unauthorized Please Login First"
        command = f"send {self.tokenid} {usernameto} {message} \r\n"
        response = self.sendstring(command)
        if response['status']=='OK':
            return "sent to {}" . format(usernameto)
        else:
            return "Error, {}" . format(response['message'])

    def send_group_message(self,usernames="xxx",message="xxx"):
        if not self.tokenid:
            return "Error, Unauthorized Please Login First "
        command = f"sendgroup {self.tokenid} {usernames} {message} \r\n"
        response = self.sendstring(command)
        if response['status']=='OK':
            return "sent to {}" . format(usernames)
        else:
            return "Error, {}" . format(response['message'])

    def _send_message(self, message):
        self.sock.sendall(message.encode())

    def _send_file(self, file_path):
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        self._send_message(f"sendfile {file_name} {file_size}")

        with open(file_path, "rb") as file:
            data = file.read(1024)
            while data:
                self.sock.sendall(data)
                data = file.read(1024)

        received_file_path = os.path.join(self.direktori_save, file_name)
        with open(received_file_path, "wb") as received_file:
            while file_size > 0:
                data = self.sock.recv(1024)
                received_file.write(data)
                file_size -= len(data)

        print(f"File '{file_name}' received and saved in '{received_file_path}'")
        
    def inbox(self):
        if not self.tokenid:
           return "Error, Unauthorized Please Login First"
        command = f"inbox {self.tokenid}\r\n"
        response = self.sendstring(command)
        if response['status']=='OK':
            return "{}" . format(json.dumps(response['messages']))
        else:
            return "Error, {}" . format(response['message'])
        
    def add_realm_connect(self, realm_ID, realm_address, realm_port):
        if not self.tokenid:
            return "Error, Unauthorized Please Login First"
        command = f"addrealm {realm_ID} {realm_address} {realm_port} \r\n"
        response = self.sendstring(command)
        if response['status']=='OK':
            return "Realm {} added" . format(realm_ID)
        else:
            return "Error, {}" . format(response['message'])
        
    def send_realm_message(self, realm_ID, username_to, message):
        if not self.tokenid:
            return "Error, Unauthorized Please Login First"
        command = f"sendrealm {self.tokenid} {realm_ID} {username_to} {message} \r\n"
        response = self.sendstring(command)
        if response['status']=='OK':
            return "sent to realm {}".format(realm_ID)
        else:
            return "Error, {}".format(response['message'])
        
    def send_group_realm_message(self, realm_ID, usernames, message):
        if not self.tokenid:
            return "Error, Unauthorized Please Login First"
        command = f"sendrealmgroup {self.tokenid} {realm_ID} {usernames} {message} \r\n"
        response = self.sendstring(command)
        if response['status']=='OK':
            return "sent to group {} in realm {}" .format(usernames, realm_ID)
        else:
            return "Error {}".format(response['message'])

    def inbox_realm(self, realm_ID):
        if not self.tokenid:
            return "Error, Unauthorized Please Login First"
        command = f"inboxrealm {self.tokenid} {realm_ID} \r\n"
        response = self.sendstring(command)
        print("Received: " + str(response))
        if response['status']=='OK':
            return "received from realm {}: {}".format(realm_ID, response['messages'])
        else:
            return "Error, {}".format(response['message'])

if __name__=="__main__":
    cc = ChatClient()

    while True:
        print("\n")
        cmdline = input("Command {}:" . format(cc.tokenid))
        print(cc.proses(cmdline))