# | Created by Ar4ikov
# | Время: 16.02.2019 - 19:29

from os import path
from sqlite3 import connect

database = connect(path.abspath(".") + "/WebRequests.db", check_same_thread=False)
cursor = database.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS access_tokens (
  id INTEGER PRIMARY KEY AUTOINCREMENT ,
  server_id TEXT NOT NULL ,
  member_id TEXT NOT NULL ,
  access_token TEXT NOT NULL ,
  when_created DATE NOT NULL
);
""")

database.commit()
