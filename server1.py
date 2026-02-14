import socket
import threading
import json
import os
import atexit
import uuid
from datetime import datetime

HOST = '0.0.0.0'
PORT = 5555

DATA_FILE = 'chat_data.json'
UPLOADS_DIR = 'uploads'

clients = []                # faol client socketlari
usernames = {}              # socket → username

# JSON ma'lumotlarni yuklash / saqlash
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'messages': []}
    return {'messages': []}

def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

data = load_data()

# Server yopilganda tozalash
def cleanup():
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    if os.path.exists(UPLOADS_DIR):
        for filename in os.listdir(UPLOADS_DIR):
            try:
                os.remove(os.path.join(UPLOADS_DIR, filename))
            except:
                pass
        try:
            os.rmdir(UPLOADS_DIR)
        except:
            pass
    print("[SERVER] Tozalandi → JSON va uploads o'chirildi")
atexit.register(cleanup)

os.makedirs(UPLOADS_DIR, exist_ok=True)

def broadcast(message, sender_socket=None):
    """Barcha clientlarga yuborish (o'ziga yubormaslik mumkin)"""
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message.encode('utf-8'))
            except:
                pass

def handle_client(client_socket, addr):
    print(f"[YANGI ULANGAN] {addr}")
    username = "Foydalanuvchi"

    try:
        # Birinchi xabar → username deb qabul qilamiz (oddiy variant)
        client_socket.send("Ismingizni kiriting: ".encode('utf-8'))
        username_data = client_socket.recv(1024).decode('utf-8').strip()
        if username_data:
            username = username_data
        usernames[client_socket] = username
        join_msg = f"[{username}] chatga qo'shildi"
        print(join_msg)
        broadcast(join_msg)
    except:
        client_socket.close()
        return

    clients.append(client_socket)

    while True:
        try:
            raw_data = client_socket.recv(4096)
            if not raw_data:
                break

            try:
                message = raw_data.decode('utf-8')
                if message.lower() in ['exit', 'quit', 'chiqish']:
                    break

                full_msg = f"[{username}] {message}"
                print(full_msg)
                data['messages'].append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "user": username,
                    "text": message
                })
                save_data(data)
                broadcast(full_msg, client_socket)
            except UnicodeDecodeError:
                # Fayl yuborilgan bo'lishi mumkin
                # Birinchi 4 bayt → "FILE"
                if raw_data.startswith(b"FILE"):
                    try:
                        header_end = raw_data.find(b"|")
                        if header_end == -1:
                            continue
                        header = raw_data[4:header_end].decode('utf-8')
                        file_data = raw_data[header_end+1:]

                        ext = os.path.splitext(header)[1].lower()
                        file_id = f"{uuid.uuid4()}{ext}"
                        file_path = os.path.join(UPLOADS_DIR, file_id)

                        with open(file_path, 'wb') as f:
                            f.write(file_data)

                        file_msg = f"[Fayl] {username} → {header} (ID: {file_id})"
                        print(file_msg)
                        data['messages'].append({
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "user": username,
                            "type": "file",
                            "filename": header,
                            "file_id": file_id
                        })
                        save_data(data)
                        broadcast(file_msg, client_socket)
                    except Exception as e:
                        print(f"Fayl xatosi: {e}")
        except:
            break

    # Chiqish
    clients.remove(client_socket)
    del usernames[client_socket]
    leave_msg = f"[{username}] chiqib ketdi"
    print(leave_msg)
    broadcast(leave_msg)
    client_socket.close()

# Serverni ishga tushirish
def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"Server ishlamoqda → {HOST}:{PORT}")

    while True:
        try:
            client_socket, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\n[SERVER] To'xtatildi (Ctrl+C)")
            break
        except Exception as e:
            print(f"Server xatosi: {e}")
            break

    server.close()
    print("[SERVER] To'liq to'xtadi")

if __name__ == "__main__":
    main()