import os
import json
import shutil
from datetime import datetime, timedelta
from Crypto.Cipher import DES3
import sqlite3, base64


# Fungsi untuk mengonversi format tanggal dan waktu Firefox ke objek datetime Python
def get_firefox_datetime(firefoxdate):
    return datetime(1970, 1, 1) + timedelta(microseconds=firefoxdate)


# Fungsi untuk mendapatkan kunci enkripsi dari file "key4.db" dalam instalasi Firefox
def get_encryption_key():
    try:
        # Path ke direktori profil pengguna Firefox
        firefox_profile_path = os.path.join(os.environ["APPDATA"], "Mozilla", "Firefox", "Profiles")

        # Temukan direktori profil pengguna Firefox
        profile_dirs = [d for d in os.listdir(firefox_profile_path) if
                        os.path.isdir(os.path.join(firefox_profile_path, d))]
        if profile_dirs:
            profile_dir = os.path.join(firefox_profile_path, profile_dirs[0])
            key_db_path = os.path.join(profile_dir, "key4.db")

            # Terhubung ke basis data kunci Firefox
            conn = sqlite3.connect(key_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT item1, item2 FROM metadata WHERE id = 'password';")
            row = cursor.fetchone()

            # Item1 adalah salt, dan item2 adalah kunci enkripsi yang dienkripsi dengan kunci master
            # Selain itu, gunakan Python 3.8 ke atas
            key = base64.b64decode(row[1])
            salt = base64.b64decode(row[0])
            kdf_data = key + b"Mozilla" + salt
            kdf_key = os.urandom(32)

            # Derive key menggunakan PBKDF2
            kdf_cipher = DES3.new(kdf_key, DES3.MODE_CBC, salt[:8])
            derived_key = kdf_cipher.encrypt(kdf_data)[:24]

            # Hapus DPAPI str
            return derived_key[5:]
    except Exception as e:
        print(f"Gagal mendapatkan kunci enkripsi: {e}")
    return None


# Fungsi untuk mendekripsi kata sandi yang dienkripsi dalam basis data Firefox
def decrypted_password(password, key):
    try:
        # Ambil IV dari 3 karakter pertama password
        iv = password[:3].decode("latin-1")
        password = password[3:]

        # Hasilkan sandi
        cipher = DES3.new(key, DES3.MODE_OFB, iv)

        # Dekripsi kata sandi
        decrypted_password = cipher.decrypt(password).decode("utf-8")

        # Hapus karakter padding
        return decrypted_password.rstrip('\x00')
    except Exception as e:
        print(f"Gagal mendekripsi kata sandi: {e}")
    return ""


# Fungsi utama untuk mengekstrak dan menampilkan informasi login dari basis data Firefox
def main():
    # Dapatkan kunci enkripsi Firefox
    key = get_encryption_key()

    if key is None:
        print("Gagal mendapatkan kunci enkripsi Firefox.")
        return

    # Path basis data lokal Firefox SQLite
    db_path_firefox = os.path.join(os.environ["APPDATA"], "Mozilla", "Firefox", "Profiles", "*", "logins.json")

    # Salin file ke lokasi lain karena basis data dapat terkunci jika Firefox sedang berjalan
    filename_firefox = "FirefoxData.json"
    try:
        shutil.copyfile(db_path_firefox, filename_firefox)
    except FileNotFoundError:
        print("File basis data Firefox tidak ditemukan.")
        exit()

    # Baca dan muat data dari file JSON
    with open(filename_firefox, "r", encoding="utf-8") as file:
        logins_data_firefox = json.load(file)

    # Iterasi semua entri login
    for entry in logins_data_firefox["logins"]:
        origin_url = entry["origin_url"]
        action_url = entry["action_url"]
        username = entry["username"]
        encrypted_password = entry["encryptedPassword"]
        date_created = entry["timeCreated"]
        date_last_used = entry["timeLastUsed"]

        password = decrypted_password(encrypted_password, key)

        if username or password:
            print(f"URL Asal: {origin_url}")
            print(f"URL Aksi: {action_url}")
            print(f"Username: {username}")
            print(f"Password: {password}")
        else:
            continue

        if date_created:
            print(f"Tanggal Pembuatan: {str(get_firefox_datetime(date_created))}")

        if date_last_used:
            print(f"Terakhir Digunakan: {str(get_firefox_datetime(date_last_used))}")
        print("=" * 50)

    # Hapus file basis data yang disalin
    try:
        os.remove(filename_firefox)
    except:
        pass


# Jalankan fungsi utama jika skrip dijalankan secara langsung
if __name__ == "__main__":
    main()
