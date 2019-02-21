# | Created by Ar4ikov
# | Время: 17.02.2019 - 18:07

from os import path
from sqlite3 import connect

database = connect(path.abspath(".") + "/Essentials.db", check_same_thread=False)
cursor = database.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS mutes (
  id INTEGER PRIMARY KEY AUTOINCREMENT ,
  server_id TEXT NOT NULL ,
  member_id TEXT NOT NULL ,
  muted_by TEXT,
  when_muted DATE NOT NULL ,
  mute_reset_after INTEGER NOT NULL 
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS `mute_roles` (
  id INTEGER PRIMARY KEY AUTOINCREMENT ,
  server_id TEXT NOT NULL ,
  role_id TEXT NOT NULL ,
  created_by TEXT NOT NULL 
);
""")

database.commit()
