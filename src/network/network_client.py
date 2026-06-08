import socket
import threading
import json
import logging
from queue import Queue, Empty

class NetworkClient:
    def __init__(self, host='127.0.0.1', port=7777):
        self.host = host
        self.port = port
        self.sock = None
        self.is_connected = False
        self.is_host = False
        self.room_code = None
        
        self.receive_queue = Queue()
        self._receive_thread = None
        self._stop_event = threading.Event()

    def connect(self):
        if self.is_connected: return True
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(1.5) # Connection timeout
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(None) # Blocking mode for thread
            self.is_connected = True
            
            self._stop_event.clear()
            self._receive_thread = threading.Thread(target=self._receive_loop)
            self._receive_thread.daemon = True
            self._receive_thread.start()
            return True
        except Exception as e:
            logging.error(f"Failed to connect to relay server: {e}")
            return False

    def disconnect(self):
        self.is_connected = False
        self._stop_event.set()
        if self.sock:
            try:
                self.sock.close()
            except:
                pass

    def create_room(self):
        if not self.is_connected: return False
        self.send({"cmd": "create_room"})
        return True

    def join_room(self, room_code):
        if not self.is_connected: return False
        self.send({"cmd": "join_room", "room_code": room_code})
        return True

    def send(self, data: dict):
        if not self.is_connected or not self.sock: return
        try:
            msg = json.dumps(data) + "\n"
            self.sock.sendall(msg.encode('utf-8'))
        except Exception as e:
            logging.error(f"Error sending data: {e}")
            self.disconnect()

    def _receive_loop(self):
        buffer = ""
        while not self._stop_event.is_set():
            try:
                data = self.sock.recv(8192)
                if not data:
                    self.disconnect()
                    break
                    
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if not line.strip(): continue
                    try:
                        packet = json.loads(line)
                        self._handle_internal_packet(packet)
                    except json.JSONDecodeError:
                        pass
                        
            except socket.timeout:
                continue
            except Exception as e:
                if not self._stop_event.is_set():
                    logging.error(f"Error receiving data: {e}")
                self.disconnect()
                break

    def _handle_internal_packet(self, packet):
        cmd = packet.get("cmd")
        if cmd == "room_created":
            self.room_code = packet.get("room_code")
            self.is_host = True
            logging.info(f"Room created: {self.room_code}")
        elif cmd == "room_joined":
            self.room_code = packet.get("room_code")
            self.is_host = False
            logging.info(f"Joined room: {self.room_code}")
            
        # Put all packets into queue for the main thread to process safely
        self.receive_queue.put(packet)

    def get_messages(self):
        messages = []
        while True:
            try:
                msg = self.receive_queue.get_nowait()
                messages.append(msg)
            except Empty:
                break
        return messages

# Global singleton
net_client = NetworkClient()
