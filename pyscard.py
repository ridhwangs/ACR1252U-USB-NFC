import sys
import tkinter as tk
from tkinter import Listbox, Scrollbar
from smartcard.System import readers
from smartcard.util import toHexString
import threading
import time

try:
    if sys.platform.startswith("linux"):
        import pyudev  # Untuk deteksi perubahan USB di Linux
        USE_UDEV = True
    else:
        USE_UDEV = False
except ImportError:
    USE_UDEV = False

class NFCReaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NFC Reader")
        self.root.geometry("500x250")  # Tinggi dikurangi agar lebih compact
        self.root.resizable(False, False)  # Matikan resize

        self.label = tk.Label(root, text="Menunggu NFC Reader...", font=("Arial", 12))
        self.label.pack(pady=5)  # Kurangi padding agar lebih compact

        # Frame untuk listbox dan scrollbar agar sejajar
        frame = tk.Frame(root)
        frame.pack(pady=0, fill="both", expand=True)  # Hapus padding bawah

        self.listbox = Listbox(frame, width=60, height=8)  # Kurangi tinggi listbox
        self.listbox.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = Scrollbar(frame, orient="vertical", command=self.listbox.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.listbox.config(yscrollcommand=self.scrollbar.set)

        self.running = True
        self.current_reader = None  # Menyimpan reader yang digunakan

        if USE_UDEV:
            self.reader_thread = threading.Thread(target=self.monitor_usb_linux, daemon=True)
        else:
            self.reader_thread = threading.Thread(target=self.monitor_usb_windows, daemon=True)

        self.reader_thread.start()

    def monitor_usb_windows(self):
        """Loop untuk mengecek apakah NFC reader terhubung atau tidak (Windows)"""
        last_status = None
        while self.running:
            available_readers = readers()
            if available_readers:
                if last_status != "connected":
                    self.current_reader = available_readers[0]
                    self.root.after(0, self.update_label, f"Reader terdeteksi: {self.current_reader}")
                    self.start_nfc_monitor(self.current_reader)
                    last_status = "connected"
            else:
                if last_status != "disconnected":
                    self.current_reader = None
                    self.root.after(0, self.update_label, "NFC Reader dicabut! Harap colokkan kembali.")
                    last_status = "disconnected"
            time.sleep(2)

    def monitor_usb_linux(self):
        """Memantau perubahan USB dengan udev (Linux)"""
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem="usb")

        for device in monitor:
            if device.action == "add":
                available_readers = readers()
                if available_readers:
                    self.current_reader = available_readers[0]
                    self.root.after(0, self.update_label, f"Reader terdeteksi: {self.current_reader}")
                    self.start_nfc_monitor(self.current_reader)
            elif device.action == "remove":
                self.current_reader = None
                self.root.after(0, self.update_label, "NFC Reader dicabut! Harap colokkan kembali.")

    def start_nfc_monitor(self, reader):
        """Membaca kartu NFC saat reader terhubung"""
        while self.running and self.current_reader:
            try:
                connection = reader.createConnection()
                connection.connect()
                get_uid_command = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                data, sw1, sw2 = connection.transmit(get_uid_command)

                if sw1 == 0x90 and sw2 == 0x00:
                    uid = toHexString(data)
                    self.root.after(0, self.update_listbox, f"UID Kartu: {uid}")
                else:
                    self.root.after(0, self.update_listbox, f"Kesalahan membaca kartu: SW1={sw1} SW2={sw2}")

            except Exception:
                time.sleep(0.5)
                continue

            finally:
                connection.disconnect()
                time.sleep(1)

    def update_label(self, text):
        self.label.config(text=text)

    def update_listbox(self, text):
        self.listbox.insert(tk.END, text)
        self.listbox.yview(tk.END)  # Selalu scroll ke bawah jika ada data baru

if __name__ == "__main__":
    root = tk.Tk()
    app = NFCReaderApp(root)
    root.mainloop()
