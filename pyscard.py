from smartcard.System import readers
from smartcard.util import toHexString
import time

def monitor_nfc():
    try:
        # Mendapatkan daftar reader yang tersedia
        available_readers = readers()
        if not available_readers:
            print("Tidak ada NFC reader yang terdeteksi!")
            return

        # Menggunakan reader pertama
        reader = available_readers[0]
        print(f"Menggunakan reader: {reader}")

        # Loop untuk mendeteksi kartu NFC
        while True:
            connection = reader.createConnection()
            try:
                # Mencoba koneksi ke kartu
                connection.connect()

                # Jika berhasil, kirim APDU untuk membaca UID kartu
                get_uid_command = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                data, sw1, sw2 = connection.transmit(get_uid_command)

                if sw1 == 0x90 and sw2 == 0x00:
                    print(f"UID Kartu: {toHexString(data)}")
                else:
                    print(f"Kesalahan membaca kartu: SW1={sw1} SW2={sw2}")

            except Exception:
                # Jika kartu tidak ditemukan, tunggu dan coba lagi
                time.sleep(0.5)
                continue

            finally:
                connection.disconnect()
                print("Menunggu kartu berikutnya...\n")
                time.sleep(1)  # Jeda sebelum mencoba membaca kartu lagi

    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    monitor_nfc()
