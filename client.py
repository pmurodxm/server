import socket
import threading
import sys
from colorama import init, Fore, Style

# Windows uchun ranglarni yoqamiz
init(autoreset=True)

# Har xil ranglar ro'yxati (navbat bilan ishlatiladi)
COLORS = [
    Fore.GREEN,
    Fore.YELLOW,
    Fore.CYAN,
    Fore.MAGENTA,
    Fore.BLUE,
    Fore.LIGHTRED_EX,
    Fore.LIGHTGREEN_EX,
    Fore.LIGHTCYAN_EX,
    Fore.LIGHTMAGENTA_EX,
    Fore.LIGHTBLUE_EX,
]

color_index = 0  # global indeks – har safar oshiriladi

def receive():
    global color_index
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message:
                color = COLORS[color_index % len(COLORS)]
                print(f"{color}{message}{Style.RESET_ALL}", end='')
                color_index += 1
            else:
                break
        except:
            break

def write():
    while True:
        try:
            message = input("")
            if message.lower() in ['exit', 'quit', 'chiqish']:
                client.send('exit'.encode('utf-8'))
                break
            if message.strip():
                client.send(message.encode('utf-8'))
        except:
            break

if __name__ == "__main__":
    # ASCII art va sarlavha
    print("\n" + "═" * 70)
    print("""
▄▄▄█████▓▓█████ ██▓ ▓█████ ▄████ ██▀███ ▄▄▄       ███▄ ▄███▓ ██░ ██ ▄▄▄     ▄████▄   ██ ▄█▀
▓██▒ ▓▒▓█ ▀ ▓██▒ ▓█ ▀ ██▒ ▀█▒▓██ ▒ ██▒▒████▄    ▓██▒▀█▀ ██▒ ▓██░ ██▒▒████▄  ▒██▀ ▀█   ██▄█▒ 
▒ ▓██░ ▒░▒███ ▒██░ ▒███ ▒██░▄▄▄░▓██ ░▄█ ▒▒██  ▀█▄  ▓██    ▓██░ ▒██▀▀██░▒██  ▀█▄ ▒▓█  ▄  ▓███▄░ 
░ ▓██▓ ░ ▒▓█  ▄ ▒██░ ▒▓█  ▄ ░▓█  ██▓▒██▀▀█▄  ░██▄▄▄▄██ ▒██    ▒██ ░▓█ ░██ ░██▄▄▄▄██ ▒▓▓▄ ▄██▒▓██ █▄
  ▒██▒ ░ ░▒████▒░██████▒░▒████▒░▒▓███▀▒░██▓ ▒██▒ ▓█   ▓██▒▒██▒   ░██▒ ▓█▒░██▓ ▓█   ▓██▒▒ ▓███▀ ░▒██▒ █▄
  ▒ ░░   ░░ ▒░ ░░ ▒░▓  ░░░ ▒░ ░ ░▒ ▒  ░▓ ░▒▓░ ▒▒ ▓▒█░░ ▒░   ░ ▒░ ▒ ░░▒░▒ ▒▒ ▓▒█░░ ░▒ ▒  ░ ▒▒ ▓▒
    ░     ░░ ░  ░░ ░ ▒  ░ ░ ░  ░ ░  ▒   ▒ ░ ▒░ ░ ░ ▒ ░▒░  ░ ▒ ░ ░   ░░ ░ ▒ ▒▒ ░ ░  ▒  ░ ░ ▒ 
  ░ ░       ░     ░ ░      ░  ░      ░   ░   ░    ░ ░  ░░ ░ ░  ░    ░  ░ ░ ░  ░      ░ ░ 
            ░  ░    ░  ░   ░  ░ ░         ░     ░  ░     ░        ░      ░            ░ 
""".strip())
    print("                     TERMINAL CHAT CLIENT".center(70))
    print("═" * 70 + "\n")

    # Avtomatik lokal IP topish
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except:
        local_ip = "127.0.0.1"

    print(f"  Avtomatik topilgan IP:  {local_ip}")
    print("  Agar server o'z kompyuteringizda bo'lsa → localhost yoki Enter bosing")
    print("  Boshqa kompyuterda bo'lsa → o'sha kompyuterning IP manzilini kiriting\n")

    HOST = input("  Server IP yoki 'localhost' kiriting (majburiy): ").strip()

    if not HOST:
        HOST = local_ip
    elif HOST.lower() in ['l', 'local', 'localhost']:
        HOST = "127.0.0.1"

    if not HOST:
        print("\nXato: Server IP manzili kiritilmadi!")
        sys.exit(1)

    # Port majburiy
    port_input = input("  Port raqami (masalan 7777): ").strip()

    if not port_input.isdigit() or not port_input:
        print("\nXato: To'g'ri port raqami kiritilmadi!")
        print("Masalan: 7777, 5000, 12345 kabi raqam kiriting")
        sys.exit(1)

    PORT = int(port_input)

    print(f"\n  Ulanmoqda... → {HOST}:{PORT}\n")

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((HOST, PORT))
        print("  Ulandi! Yozishni boshlang (chiqish uchun: exit yoki quit)\n")
    except Exception as e:
        print(f"  Xato: Ulanib bo'lmadi → {e}")
        print("  Tekshirish kerak:")
        print("  • Server ishlayaptimi?")
        print("  • IP va port to'g'rimi?")
        print("  • Firewall bloklamayaptimi?")
        sys.exit(1)

    # Qabul qiluvchi thread
    receive_thread = threading.Thread(target=receive, daemon=True)
    receive_thread.start()

    # Yozuvchi qism (asosiy oqim)
    write()

    client.close()
    print("\n  Suhbat tugadi.")