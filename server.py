import socket
import threading

HOST = ''          # barcha interfeyslardan qabul qilish uchun
PORT = 5551               # o'zingiz xohlagan port (1024 dan katta bo'lsin)
clients = []              # ulangan barcha mijozlar

def broadcast(message, sender=None):
    for client in clients:
        if client != sender:
            try:
                client.send(message)
            except:
                clients.remove(client)

def handle_client(client_socket, addr):
    print(f"→ Yangi ulanish: {addr}")
    
    # nickni so'raymiz (ixtiyoriy, lekin chiroyli bo'ladi)
    client_socket.send("Ismingizni yozing: ".encode('utf-8'))
    nickname = client_socket.recv(1024).decode('utf-8').strip()
    if not nickname:
        nickname = str(addr)

    welcome = f"{nickname} chatga kirdi!".encode('utf-8')
    broadcast(welcome)
    print(welcome.decode('utf-8'))

    while True:
        try:
            message = client_socket.recv(1024)
            if not message:
                break

            msg = message.decode('utf-8').strip()
            if msg.lower() == 'exit':
                break

            full_msg = f"{nickname} → {msg}".encode('utf-8')
            print(full_msg.decode('utf-8'))
            broadcast(full_msg, client_socket)

        except:
            break

    # chiqish
    clients.remove(client_socket)
    leave_msg = f"{nickname} chiqib ketdi.".encode('utf-8')
    broadcast(leave_msg)
    print(leave_msg.decode('utf-8'))
    
    client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(10)
    
    print(f"Server ishga tushdi → {HOST}:{PORT}")
    print("Boshqa odamlar shu IP va port bilan ulansin")
    
    while True:
        client_socket, addr = server.accept()
        clients.append(client_socket)
        
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":

    main()
