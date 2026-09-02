"""
Code snippet

This code should demonstrate detecting and verifying that a file has changed, and how the request to the server will be created.

Why did I choose this segment?

I have chosen to write a code snippet for the change detectiong as it deals with both the scanning of files, and checking to see if the file needs to be synchronised.

"""

import sqlite3
import os
import datetime
from hashlib import md5

DATABASE_NAME = "files.db"
SCRIPT_FILE_PATH = os.path.dirname(os.path.abspath(__file__))
MONITORED_DIRS = [os.path.join(SCRIPT_FILE_PATH.rsplit(os.path.sep, 1)[0], 'test_dir')]
BUF_SIZE = 65536

# Create/Connect to db
con = sqlite3.connect(DATABASE_NAME)
cur = con.cursor()
tables_found = cur.execute("SELECT name FROM sqlite_master").fetchall()
table_names = []
for table in tables_found:
    table_names.append(table[0])

# Create tables
if 'files' not in table_names:
    cur.execute("CREATE TABLE files(file_path, file_hash, time_last_change, time_last_successful_sync, to_sync)")
if 'last_run' not in table_names:
    cur.execute("CREATE TABLE last_run(time_last_run)")

for path in MONITORED_DIRS:
    for file in os.listdir(path):

        # Find if file already exists in database
        file_exists = False
        previously_found_files = cur.execute("SELECT file_path FROM files")

        # Get only the file names (result from above is in a tuple of (name, ''))
        found_file_names = []
        for found_file in previously_found_files:
            found_file_names.append(found_file[0])
        file_path = os.path.join(path, file)
        if file_path in found_file_names:
            file_exists = True
        last_modified_time = os.path.getmtime(file_path)
        if file_exists:
            # Check if file has been modified since last scan
            # This is a quicker way to check instead of comparing hashes for large files. It could be best to compare both time and hashes if there is a chance for the OS to give the wrong modified time.
            db_last_modified_time = cur.execute(f"SELECT time_last_change FROM files WHERE file_path = '{file_path}'").fetchone()[0]
            if last_modified_time == db_last_modified_time:
                # File has not been modified
                continue

        # Get md5 hash of file
        raw_file_hash = md5()
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                raw_file_hash.update(data)
        file_hash = raw_file_hash.hexdigest()

        # Save to database
        if file_exists == False:
            cur.execute(f"INSERT INTO files VALUES ('{file_path}', '{file_hash}', '{last_modified_time}', 'NULL', 'Y')")
        else:
            # File has been modified, save to database
            cur.execute(f"UPDATE files SET file_hash = '{file_hash}', time_last_change = '{last_modified_time}', to_sync = 'Y' WHERE file_path = '{file_path}'")
        con.commit()

res = cur.execute("SELECT * FROM files")
for row in res.fetchall():
    print(row)

con.close()

