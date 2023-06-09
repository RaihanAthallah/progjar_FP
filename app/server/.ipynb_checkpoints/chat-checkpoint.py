import base64
import os
import json
import uuid
import logging
from queue import  Queue
import threading 
import socket

class RealmCommunicationThread(threading.Thread):
    def __init__(self, chats, realm_dest_address, realm_dest_port):
        self.chats = chats
        self.chat = {}
        self.realm_dest_address = realm_dest_address
        self.realm_dest_port = realm_dest_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.realm_dest_address, self.realm_dest_port))
        threading.Thread.__init__(self)

    def sendstring(self, string):
        try:
            self.sock.sendall(string.encode())
            receivedmsg = ""
            while True:
                data = self.sock.recv(1024)
                print("diterima dari server", data)
                if (data):
                    receivedmsg = "{}{}" . format(receivedmsg, data.decode())  #data harus didecode agar dapat di operasikan dalam bentuk string
                    if receivedmsg[-4:]=='\r\n\r\n':
                        print("end of string")
                        return json.loads(receivedmsg)
        except:
            self.sock.close()
            return { 'status' : 'ERROR', 'message' : 'Fail'}
    
    def put(self, message):
        dest = message['msg_to']
        try:
            self.chat[dest].put(message)
        except KeyError:
            self.chat[dest]=Queue()
            self.chat[dest].put(message)

class Chat:
    def __init__(self):
        self.sessions={}
        self.users = {}
        self.users['messi']={ 'nama': 'Lionel Messi', 'negara': 'Argentina', 'password': 'surabaya', 'incoming' : {}, 'outgoing': {}}
        self.users['henderson']={ 'nama': 'Jordan Henderson', 'negara': 'Inggris', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}}
        self.users['raihan']={ 'nama': 'raihan', 'negara': 'Indonesia', 'password': 'surabaya','incoming': {}, 'outgoing':{}}
        self.users['malik']={ 'nama': 'malik', 'negara': 'Indonesia', 'password': 'surabaya','incoming': {}, 'outgoing':{}}
        self.users['ijat']={ 'nama': 'ijat', 'negara': 'Indonesia', 'password': 'surabaya','incoming': {}, 'outgoing':{}}
        self.users['ichlas']={ 'nama': 'ichlas', 'negara': 'Indonesia', 'password': 'surabaya','incoming': {}, 'outgoing':{}}
        self.users['ghani']={ 'nama': 'ghani', 'negara': 'Indonesia', 'password': 'surabaya','incoming': {}, 'outgoing':{}}
        self.users['eca']={ 'nama': 'eca', 'negara': 'Indonesia', 'password': 'surabaya','incoming': {}, 'outgoing':{}}
        self.realms = {}
    def proses(self,data):
        j=data.split(" ")
        try:
            command=j[0].strip()
            if (command=='auth'):
                username=j[1].strip()
                password=j[2].strip()
                logging.warning("AUTH: auth {} {}" . format(username,password))
                return self.autentikasi_user(username,password)        
            elif (command=='send'):
                sessionid = j[1].strip()
                usernameto = j[2].strip()
                message=""
                for w in j[3:]:
                    message="{} {}" . format(message,w)
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("session {} send message from {} to {}" . format(sessionid, usernamefrom,usernameto))
                return self.send_message(sessionid,usernamefrom,usernameto,message)
            elif command == 'recvfile':  # New command for receiving a file
                sessionid = j[1].strip()
                filepath = j[2].strip()
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("session {} receive file from {}" . format(sessionid, usernamefrom))
                return self.receive_file(sessionid, usernamefrom, filepath)
            elif (command=='sendgroup'):
                sessionid = j[1].strip()
                usernamesto = j[2].strip().split(',')
                message=""
                for w in j[3:]:
                    message="{} {}" . format(message,w)
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("session {} send message from {} to {}" . format(sessionid, usernamefrom,usernamesto))
                return self.send_group_message(sessionid,usernamefrom,usernamesto,message)
            elif (command=='inbox'):
                sessionid = j[1].strip()
                username = self.sessions[sessionid]['username']
                logging.warning("INBOX: {}" . format(sessionid))
                return self.get_inbox(username)
            elif (command=='sendgroupfile'):
                sessionid = j[1].strip()
                usernamesto = j[2].strip().split(',')
                filepath = j[3].strip()
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("session {} send file from {} to {}" . format(sessionid, usernamefrom, usernamesto))
                return self.send_group_file(sessionid, usernamefrom, usernamesto, filepath)       
            elif (command=='addrealm'):
                realm_id = j[1].strip()
                realm_dest_address = j[2].strip()
                realm_dest_port = int(j[3].strip())
                return self.add_realm(realm_id, realm_dest_address, realm_dest_port, data)
            elif (command=='recvrealm'):
                realm_id = j[1].strip()
                realm_dest_address = j[2].strip()
                realm_dest_port = int(j[3].strip())
                return self.recv_realm(realm_id, realm_dest_address, realm_dest_port, data)
            elif (command == 'sendprivaterealm'):
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernameto = j[3].strip()
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w)
                print(message)
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("session {} send message from {} to {} in realm {}".format(sessionid, usernamefrom, usernameto, realm_id))
                return self.send_realm_message(sessionid, realm_id, usernamefrom, usernameto, message, data)
            elif (command == 'recvrealmprivatemsg'):
                usernamefrom = j[1].strip()
                realm_id = j[2].strip()
                usernameto = j[3].strip()
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w)
                print(message)
                logging.warning("recieve message from {} to {} in realm {}".format( usernamefrom, usernameto, realm_id))
                return self.recv_realm_message(realm_id, usernamefrom, usernameto, message, data)
            elif (command == 'sendgrouprealm'):
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernamesto = j[3].strip().split(',')
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w)
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("session {} send message from {} to {} in realm {}".format(sessionid, usernamefrom, usernamesto, realm_id))
                return self.send_group_realm_message(sessionid, realm_id, usernamefrom,usernamesto, message,data)
            elif (command == 'sendgroupfilerealm'):
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernamesto = j[3].strip().split(',')
                filepath = j[4].strip()
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("session {} send file from {} to {} in realm {}".format(sessionid, usernamefrom, usernamesto, realm_id))
                return self.send_group_file_realm(sessionid, realm_id, usernamefrom,usernamesto, filepath, data)
            elif (command == 'recvrealmgroupmsg'):
                usernamefrom = j[1].strip()
                realm_id = j[2].strip()
                usernamesto = j[3].strip().split(',')
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w) 
                logging.warning("send message from {} to {} in realm {}".format(usernamefrom, usernamesto, realm_id))
                return self.recv_group_realm_message(realm_id, usernamefrom,usernamesto, message,data)
            elif (command == 'getrealminbox'):
                sessionid = j[1].strip()
                realmid = j[2].strip()
                username = self.sessions[sessionid]['username']
                logging.warning(" {} from realm {}".format(sessionid, realmid))
                return self.get_realm_inbox(username, realmid)
            elif (command == 'getrealmchat'):
                realmid = j[1].strip()
                username = j[2].strip()
                logging.warning(" from realm {}".format(realmid))
                return self.get_realm_chat(realmid, username)
            else:
                print(command)
                return {'status': 'ERROR', 'message': '**Incorrect Protocol !'}
        except KeyError:
            return { 'status': 'ERROR', 'message' : 'Information Not Found !'}
        except IndexError:
            return {'status': 'ERROR', 'message': '--Incorrect Protocol !'}

    def autentikasi_user(self,username,password):
        if (username not in self.users):
            return { 'status': 'ERROR', 'message': 'User Not Found !' }
        if (self.users[username]['password']!= password):
            return { 'status': 'ERROR', 'message': 'Wrong Password !' }
        tokenid = str(uuid.uuid4()) 
        self.sessions[tokenid]={ 'username': username, 'user_detail':self.users[username]}
        return { 'status': 'OK', 'tokenid': tokenid }

    def get_user(self,username):
        if (username not in self.users):
            return False
        return self.users[username]

    def send_message(self,sessionid,username_from,username_dest,message):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Not Found !'}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)

        if (s_fr==False or s_to==False):
            return {'status': 'ERROR', 'message': 'User Not Found !'}

        message = { 'msg_from': s_fr['nama'], 'msg_to': s_to['nama'], 'msg': message }
        outqueue_sender = s_fr['outgoing']
        inqueue_receiver = s_to['incoming']
        try:	
            outqueue_sender[username_from].put(message)
        except KeyError:
            outqueue_sender[username_from]=Queue()
            outqueue_sender[username_from].put(message)
        try:
            inqueue_receiver[username_from].put(message)
        except KeyError:
            inqueue_receiver[username_from]=Queue()
            inqueue_receiver[username_from].put(message)
        return {'status': 'OK', 'message': 'Message Sent'}
        
    def receive_file(self, sessionid, usernamefrom, filepath):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Not Found !'}
        
        s_fr = self.get_user(usernamefrom)
        if s_fr is False:
            return {'status': 'ERROR', 'message': 'User Not Found !'}
    
        inqueue_receiver = s_fr['incoming']
        try:
            file_message = inqueue_receiver[usernamefrom].get_nowait()
            if 'file_name' not in file_message or 'file_content' not in file_message:
                return {'status': 'ERROR', 'message': 'Invalid file message'}
            
            file_name = file_message['file_name']
            file_content = file_message['file_content']
            
            file_data = base64.urlsafe_b64decode(file_content.encode('utf-8'))
    
            with open(filepath, 'wb') as file:
                file.write(file_data)
    
            return {'status': 'OK', 'message': 'File Received'}
        except KeyError:
            return {'status': 'ERROR', 'message': 'User Not Found !'}
        except Exception as e:
            return {'status': 'ERROR', 'message': 'Error occurred while receiving file: {}'.format(str(e))}
    
    def send_group_message(self, sessionid, username_from, usernames_dest, message):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Not Found !'}
        s_fr = self.get_user(username_from)
        if s_fr is False:
            return {'status': 'ERROR', 'message': 'User Not Found !'}
        for username_dest in usernames_dest:
            s_to = self.get_user(username_dest)
            if s_to is False:
                continue
            message = {'msg_from': s_fr['nama'], 'msg_to': s_to['nama'], 'msg': message}
            outqueue_sender = s_fr['outgoing']
            inqueue_receiver = s_to['incoming']
            try:    
                outqueue_sender[username_from].put(message)
            except KeyError:
                outqueue_sender[username_from]=Queue()
                outqueue_sender[username_from].put(message)
            try:
                inqueue_receiver[username_from].put(message)
            except KeyError:
                inqueue_receiver[username_from]=Queue()
                inqueue_receiver[username_from].put(message)
        return {'status': 'OK', 'message': 'Message Sent'}
    
    def get_inbox(self,username):
        s_fr = self.get_user(username)
        incoming = s_fr['incoming']
        msgs={}
        for users in incoming:
            msgs[users]=[]
            while not incoming[users].empty():
                msgs[users].append(s_fr['incoming'][users].get_nowait())
        return {'status': 'OK', 'messages': msgs}

   
    def send_group_file(self, sessionid, username_from, usernames_dest, filepath):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Not Found !'}
        s_fr = self.get_user(username_from)
        if s_fr is False:
            return {'status': 'ERROR', 'message': 'User Not Found !'}
        if not os.path.exists(filepath):
                return {'status': 'ERROR', 'message': 'File not found'}

        with open(filepath, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.urlsafe_b64encode(file_content).decode('utf-8')  # Decode byte-string to UTF-8 string

        filename = os.path.basename(filepath)
        for username_dest in usernames_dest:
            s_to = self.get_user(username_dest)
            if s_to is False:
                continue
            message = {
                'msg_from': s_fr['nama'],
                'msg_to': s_to['nama'],
                'file_name': filename,
                'file_content': encoded_content
            }

            outqueue_sender = s_fr['outgoing']
            inqueue_receiver = s_to['incoming']
            try:
                outqueue_sender[username_from].put(json.dumps(message))
            except KeyError:
                outqueue_sender[username_from] = Queue()
                outqueue_sender[username_from].put(json.dumps(message))
            try:
                inqueue_receiver[username_from].put(json.dumps(message))
            except KeyError:
                inqueue_receiver[username_from] = Queue()
                inqueue_receiver[username_from].put(json.dumps(message))

        return {'status': 'OK', 'message': 'File Sent'}


    def add_realm(self, realm_id, realm_dest_address, realm_dest_port, data):
        j = data.split()
        j[0] = "recvrealm"
        data = ' '.join(j)
        data += "\r\n"
        if realm_id in self.realms:
            return {'status': 'ERROR', 'message': 'Realm sudah ada'}
          
        self.realms[realm_id] = RealmCommunicationThread(self, realm_dest_address, realm_dest_port)
        result = self.realms[realm_id].sendstring(data)
        return result

    def recv_realm(self, realm_id, realm_dest_address, realm_dest_port, data):
        self.realms[realm_id] = RealmCommunicationThread(self, realm_dest_address, realm_dest_port)
        return {'status':'OK'}

    def send_realm_message(self, sessionid, realm_id, username_from, username_dest, message, data):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Not Found !'}
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Not Found !'}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)
        if (s_fr==False or s_to==False):
            return {'status': 'ERROR', 'message': 'User Not Found !'}
        message = { 'msg_from': s_fr['nama'], 'msg_to': s_to['nama'], 'msg': message }
        self.realms[realm_id].put(message)
        
        j = data.split()
        j[0] = "recvrealmprivatemsg"
        j[1] = username_from
        data = ' '.join(j)
        data += "\r\n"
        self.realms[realm_id].sendstring(data)
        return {'status': 'OK', 'message': 'Message Sent to Realm'}

    def recv_realm_message(self, realm_id, username_from, username_dest, message, data):
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Not Found !'}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)
        if (s_fr==False or s_to==False):
            return {'status': 'ERROR', 'message': 'User Not Found !'}
        message = { 'msg_from': s_fr['nama'], 'msg_to': s_to['nama'], 'msg': message }
        self.realms[realm_id].put(message)
        return {'status': 'OK', 'message': 'Message Sent to Realm'}

    def send_group_realm_message(self, sessionid, realm_id, username_from, usernames_to, message, data):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Not Found !'}
        if realm_id not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Not Found !'}
        s_fr = self.get_user(username_from)
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message = {'msg_from': s_fr['nama'], 'msg_to': s_to['nama'], 'msg': message }
            self.realms[realm_id].put(message)
        
        j = data.split()
        j[0] = "recvrealmgroupmsg"
        j[1] = username_from
        data = ' '.join(j)
        data +="\r\n"
        self.realms[realm_id].sendstring(data)
        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}
    
    def send_group_file_realm(self, sessionid, realm_id, username_from, usernames_to, filepath, data):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Not Found !'}
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Not Found !'}
        s_fr = self.get_user(username_from)

        if (s_fr==False):
                return {'status': 'ERROR', 'message': 'User Not Found !'}
            
        if not os.path.exists(filepath):
            return {'status': 'ERROR', 'message': 'File not found'}

        with open(filepath, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.urlsafe_b64encode(file_content).decode('utf-8')
        
        filename = os.path.basename(filepath)

        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message = {
                'msg_from': s_fr['nama'],
                'msg_to': s_to['nama'],
                'file_name': filename,
                'file_content': encoded_content
            }
            self.realms[realm_id].put(message)
        
        j = data.split()
        j[0] = "recvrealmgroupmsg"
        j[1] = username_from
        data = ' '.join(j)
        data += "\r\n"
        self.realms[realm_id].sendstring(data)
        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}

    def recv_group_realm_message(self, realm_id, username_from, usernames_to, message, data):
        if realm_id not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Not Found !'}
        s_fr = self.get_user(username_from)
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message = {'msg_from': s_fr['nama'], 'msg_to': s_to['nama'], 'msg': message }
            self.realms[realm_id].put(message)
        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}

    def get_realm_inbox(self, username,realmid):
        if (realmid not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Not Found !'}
        s_fr = self.get_user(username)
        result = self.realms[realmid].sendstring("getrealmchat {} {}\r\n".format(realmid, username))
        return result
    def get_realm_chat(self, realmid, username):
        s_fr = self.get_user(username)
        msgs = []
        while not self.realms[realmid].chat[s_fr['nama']].empty():
            msgs.append(self.realms[realmid].chat[s_fr['nama']].get_nowait())
        return {'status': 'OK', 'messages': msgs}

if __name__=="__main__":
	j = Chat()
	sesi = j.proses("auth messi surabaya")
	print(sesi)
	#sesi = j.autentikasi_user('messi','surabaya')
	#print sesi
	tokenid = sesi['tokenid']
	print(j.proses("send {} henderson hello gimana kabarnya son " . format(tokenid)))
	print(j.proses("send {} messi hello gimana kabarnya mess " . format(tokenid)))

	#print j.send_message(tokenid,'messi','henderson','hello son')
	#print j.send_message(tokenid,'henderson','messi','hello si')
	#print j.send_message(tokenid,'lineker','messi','hello si dari lineker')


	print("isi mailbox dari messi")
	print(j.get_inbox('messi'))
	print("isi mailbox dari henderson")
	print(j.get_inbox('henderson'))
