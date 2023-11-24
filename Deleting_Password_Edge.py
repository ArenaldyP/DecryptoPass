import sqlite3
import os

db_path_edge = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                            "Microsoft", "Edge", "User Data", "Default", "Login Data")
db_edge = sqlite3.connect(db_path_edge)
cursor_edge = db_edge.cursor()
# `Login` table has the data we need
cursor_edge.execute("select origin_url, action_url, username_value, password_value, date_created,"
                    "date_last_used from logins order by date_created")
n_logins_edge = len(cursor_edge.fetchall())
print(f"Deleting a total of {n_logins_edge} Logins from Edge..")
cursor_edge.execute("delete from logins")
cursor_edge.connection.commit()
