import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, END, filedialog
import os
import sys
import pygame

# PyInstaller bilan exe bo'lganda ham fayllarni to'g'ri topish uchun
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller temp folder
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# =========================================================================
#                           Chat Client GUI
# =========================================================================

class ChatClientGUI:
    def __init__(self, master):
        self.master = master
        master.title("Chat - Mister")
        master.geometry("620x680")
        master.minsize(420, 520)
        master.resizable(True, True)

        # Ovoz tayyorlash
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.alert_sound = None
        try:
            sound_path = resource_path("alert.wav")
            self.alert_sound = pygame.mixer.Sound(sound_path)
            print("Ovoz yuklandi:", sound_path)  # debug uchun (exe da ko'rinmaydi)
        except Exception as e:
            print("Alert ovozi yuklanmadi:", e)

        # Chat maydoni
        self.chat_display = scrolledtext.ScrolledText(
            master, wrap=tk.WORD, state='disabled', font=("Segoe UI", 11),
            bg="#f8f9fa", fg="#212529", insertbackground="#000000",
            relief=tk.FLAT, borderwidth=1, padx=10, pady=10
        )
        self.chat_display.pack(padx=12, pady=12, fill=tk.BOTH, expand=True)

        # Tag konfiguratsiyalari
        self.chat_display.tag_config("me", foreground="#1e7e34", justify="right", rmargin=25,
                                     font=("Segoe UI", 11, "bold"))
        self.chat_display.tag_config("other", foreground="#0d6efd", lmargin1=10, lmargin2=10)
        self.chat_display.tag_config("file", foreground="#6f42c1", font=("Segoe UI", 10, "italic"))
        self.chat_display.tag_config("system", foreground="#dc3545", font=("Segoe UI", 10, "italic"))

        # Pastki qism - xabar yozish
        bottom_frame = tk.Frame(master, bg="#ffffff")
        bottom_frame.pack(fill=tk.X, padx=12, pady=(0, 12))

        self.msg_entry = tk.Entry(bottom_frame, font=("Segoe UI", 12), relief=tk.FLAT, bg="#f1f3f5")
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=6)
        self.msg_entry.bind("<Return>", self.send_message)

        send_btn = tk.Button(bottom_frame, text="Yuborish", font=("Segoe UI", 10, "bold"),
                             command=self.send_message, bg="#28a745", fg="white",
                             relief=tk.FLAT, padx=16, pady=6)
        send_btn.pack(side=tk.RIGHT)

        file_btn = tk.Button(master, text="📎 Rasm / GIF / Video yuborish", font=("Segoe UI", 10),
                             command=self.send_file, bg="#007bff", fg="white",
                             relief=tk.FLAT, padx=12, pady=8)
        file_btn.pack(fill=tk.X, padx=12, pady=(0, 8))

        # Chiqish tugmasi
        tk.Button(master, text="Chiqish", command=self.on_closing,
                  bg="#dc3545", fg="white", font=("Segoe UI", 10), relief=tk.FLAT,
                  padx=20, pady=8).pack(pady=(0, 12))

        self.client = None
        self.running = False
        self.username = None

        self.connect_window()

    def connect_window(self):
        win = tk.Toplevel(self.master)
        win.title("Serverga ulanish")
        win.geometry("440x340")
        win.resizable(False, False)
        win.configure(bg="#f8f9fa")

        tk.Label(win, text="Server IP yoki 'localhost':", font=("Segoe UI", 11), bg="#f8f9fa").pack(pady=(20, 5))
        self.host_var = tk.StringVar(value="127.0.0.1")
        tk.Entry(win, textvariable=self.host_var, font=("Segoe UI", 12), width=35).pack(pady=5)

        tk.Label(win, text="Port raqami:", font=("Segoe UI", 11), bg="#f8f9fa").pack(pady=(15, 5))
        self.port_var = tk.StringVar(value="7777")
        tk.Entry(win, textvariable=self.port_var, font=("Segoe UI", 12), width=35).pack(pady=5)

        tk.Label(win, text="Ismingiz:", font=("Segoe UI", 11), bg="#f8f9fa").pack(pady=(15, 5))
        self.name_var = tk.StringVar(value="Mister")
        tk.Entry(win, textvariable=self.name_var, font=("Segoe UI", 12), width=35).pack(pady=5)

        tk.Button(win, text="Ulanish", font=("Segoe UI", 11, "bold"),
                  command=lambda: self.try_connect(win),
                  bg="#28a745", fg="white", relief=tk.FLAT, padx=40, pady=10).pack(pady=25)

        win.protocol("WM_DELETE_WINDOW", self.on_closing)

    def try_connect(self, win):
        host = self.host_var.get().strip()
        port_str = self.port_var.get().strip()
        name = self.name_var.get().strip()

        if not name:
            messagebox.showwarning("Xato", "Ism kiritish majburiy!")
            return
        if not host:
            messagebox.showwarning("Xato", "Server IP / hostname kiritish majburiy!")
            return
        if not port_str.isdigit():
            messagebox.showwarning("Xato", "Port faqat raqamlardan iborat bo'lishi kerak!")
            return

        port = int(port_str)

        if host.lower() in ['l', 'local', 'localhost']:
            host = "127.0.0.1"

        self.username = name

        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((host, port))
            self.client.send(name.encode('utf-8'))
            self.running = True
            win.destroy()
            self.add_message("→ Muvaffaqiyatli ulandi!\n", "system")
            threading.Thread(target=self.receive, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Ulanish xatosi", f"Ulanib bo'lmadi:\n{e}\n\nServer ishlayaptimi?\nIP va port to'g'rimi?")

    def receive(self):
        while self.running:
            try:
                data = self.client.recv(65536)
                if not data:
                    break

                try:
                    message = data.decode('utf-8')
                    self.add_message(message + "\n", "other")
                    if self.alert_sound and message.strip() and not message.startswith(f"[{self.username}]"):
                        self.alert_sound.play()
                except UnicodeDecodeError:
                    # Fayl yoki boshqa binary (hozircha oddiy xabar sifatida)
                    pass
            except:
                break

        if self.running:
            self.add_message("\nServer bilan aloqa uzildi.\n", "system")
            self.running = False

    def send_message(self, event=None):
        if not self.running:
            return
        msg = self.msg_entry.get().strip()
        self.msg_entry.delete(0, END)
        if not msg:
            return
        if msg.lower() in ['exit', 'quit', 'chiqish']:
            try:
                self.client.send(b"exit")
            except:
                pass
            self.running = False
            self.master.after(800, self.master.quit)
            return
        try:
            self.client.send(msg.encode('utf-8'))
            self.add_message(f"[{self.username}] {msg}\n", "me")
        except:
            self.add_message("Xabar yuborishda xato\n", "system")
            self.running = False

    def send_file(self):
        if not self.running:
            return
        path = filedialog.askopenfilename(
            title="Fayl tanlang",
            filetypes=[("Media fayllar", "*.jpg *.jpeg *.png *.gif *.mp4 *.avi *.webp")]
        )
        if not path:
            return
        try:
            with open(path, 'rb') as f:
                file_data = f.read()
            filename = os.path.basename(path)
            header = f"FILE{filename}|".encode('utf-8')
            self.client.send(header + file_data)
            self.add_message(f"[{self.username}] Fayl yuborildi: {filename}\n", "me")
        except Exception as e:
            messagebox.showerror("Fayl xatosi", str(e))

    def add_message(self, text, tag="normal"):
        self.chat_display.configure(state='normal')
        self.chat_display.insert(END, text, tag)
        self.chat_display.configure(state='disabled')
        self.chat_display.see(END)

    def on_closing(self):
        if self.running and self.client:
            try:
                self.client.send(b"exit")
            except:
                pass
        self.running = False
        self.master.destroy()

# =========================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()