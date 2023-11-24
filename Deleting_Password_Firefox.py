import json
from datetime import datetime, timezone, timedelta
import os
import shutil

# Fungsi untuk mengonversi format tanggal dan waktu Firefox ke objek datetime Python
def get_firefox_datetime(firefoxdate):
    return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=firefoxdate)

# Dapatkan path profil Firefox
firefox_profile_path = os.path.join(os.environ["APPDATA"], "Mozilla", "Firefox", "Profiles")

# Temukan direktori profil Firefox
profile_dirs = [d for d in os.listdir(firefox_profile_path) if os.path.isdir(os.path.join(firefox_profile_path, d))]
if profile_dirs:
    profile_dir = os.path.join(firefox_profile_path, profile_dirs[0])
    db_path_firefox = os.path.join(profile_dir, "logins.json")

    # Salin file ke lokasi lain karena file mungkin terkunci jika Firefox sedang berjalan
    filename_firefox = "FirefoxData.json"
    try:
        shutil.copyfile(db_path_firefox, filename_firefox)
    except FileNotFoundError:
        print("File basis data Firefox tidak ditemukan.")
        exit()

    # Baca dan muat data dari file JSON
    with open(filename_firefox, "r", encoding="utf-8") as file:
        logins_data_firefox = json.load(file)

    # Hapus semua entri login dari basis data Firefox
    logins_data_firefox["logins"] = []

    # Simpan perubahan kembali ke file JSON
    with open(filename_firefox, "w", encoding="utf-8") as file:
        json.dump(logins_data_firefox, file, indent=2)

    print(f"Deleting a total of {len(logins_data_firefox['logins'])} Logins from Firefox..")
