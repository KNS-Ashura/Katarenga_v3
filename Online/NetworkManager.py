# Online/NetworkManager.py
import socket
import threading
import json
import time

class NetworkManager:
    
    def __init__(self):
        self.is_host = False
        self.is_connected = False
        self.socket = None
        self.server_socket = None
        self.clients = []
        self.message_callback = None
        self.disconnect_callback = None
        
    def set_callbacks(self, message_callback=None, disconnect_callback=None):
        self.message_callback = message_callback
        self.disconnect_callback = disconnect_callback
    
   
    def start_server(self, port=5000):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', port))
            self.server_socket.listen(1)  
            
            self.is_host = True
            self.is_connected = True
            
            # Launch thread to accept clients
            threading.Thread(target=self._accept_clients, daemon=True).start()
            
            #print(f"Server started on port: {port}")
            return True
            
        except Exception as e:
            #print(f"Unable to start server: {e}")
            return False
    
    def _accept_clients(self):
        while self.is_connected and len(self.clients) < 1:
            try:
                client_socket, client_address = self.server_socket.accept()
                self.clients.append(client_socket)
                #print(f"Client connected: {client_address}")
                
                # Launch thread to listen to this client
                threading.Thread(target=self._listen_client, args=(client_socket,), daemon=True).start()
                
            except Exception as e:
                if self.is_connected:
                    print(f"Error accepting client: {e}")
                break
    
    def _listen_client(self, client_socket):
        while self.is_connected:
            try:
                data = client_socket.recv(1024)
                if data:
                    message = data.decode('utf-8')
                    if self.message_callback:
                        self.message_callback(message)
                else:
                    break
                    
            except Exception as e:
                #print(f"Reception error: {e}")
                break
        
        # Client disconnected
        if client_socket in self.clients:
            self.clients.remove(client_socket)
        client_socket.close()
        
        if self.disconnect_callback:
            self.disconnect_callback()
                
    def connect_to_server(self, host_ip, port=5000):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host_ip, port))
            
            self.is_host = False
            self.is_connected = True
            
            # Launch thread to listen to server
            threading.Thread(target=self._listen_server, daemon=True).start()
            
            #print(f"Connected to server {host_ip}:{port}")
            return True
            
        except Exception as e:
            #print(f"Unable to connect: {e}")
            return False
        
    def _listen_server(self):
        while self.is_connected:
            try:
                data = self.socket.recv(1024)
                if data:
                    message = data.decode('utf-8')
                    if self.message_callback:
                        self.message_callback(message)
                else:
                    break
                    
            except Exception as e:
                #print(f"Reception error: {e}")
                break
        
        # Server disconnected
        self.is_connected = False
        if self.disconnect_callback:
            self.disconnect_callback()
    
    def send_message(self, message):
        if not self.is_connected:
            return False
        
        try:
            if self.is_host:
                # Send to all clients
                for client in self.clients:
                    client.send(message.encode('utf-8'))
            else:
                # Send to server
                self.socket.send(message.encode('utf-8'))
            return True
            
        except Exception as e:
            print(f"Send error: {e}")
            return False
    
    def disconnect(self):
        self.is_connected = False
        
        if self.socket:
            self.socket.close()
            self.socket = None
        
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        
        for client in self.clients:
            client.close()
        self.clients.clear()
        
        #print("Disconnected")
    
    def get_local_ip(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 80))
                return s.getsockname()[0]
        except:
            return '127.0.0.1'
    
    def get_status(self):
        return {
            'connected': self.is_connected,
            'is_host': self.is_host,
            'clients_count': len(self.clients) if self.is_host else 0,
            'local_ip': self.get_local_ip()
        }