#!/usr/bin/env python
import os
import time
import sqlite3
db_name = './trackDB.db'
schema_filename = './user.sql'

from sqlite3 import Connection
from collections import deque

class SqlClient:
    db_filename = './trackDB.db'
    db_conn = None
    #pool = None

    def __init__(self, db=db_name):
        self.db_filename = db
    def initDB(self):
        db_exists = os.path.exists(self.db_filename)
        
        with sqlite3.connect(self.db_filename, uri=True, timeout=10, check_same_thread=False) as conn:
            self.db_conn = conn
            if db_exists == None:
                print('Creating schema')
                with open(schema_filename, 'rt') as f:
                    schema = f.read()
                conn.executescript(schema)
      
    def insert_click_track(self, t1, t2, t3,mac, event, x, y, image_name):
        str_event= "{}:({},{})".format(event, x, y)
        if self.db_conn:
            cursor = self.db_conn.cursor()
            # db_conn.executescript("""
            # insert into TRACK (TIME,TIMESTEMP,EVENT,POINT_X,POINT_Y,IMG_PATH)
            # values (t, t, event, x, y, image_name);
            # """)
            cursor.execute('''
            INSERT INTO TRACK (TIME,TIMESTEMP, TIMEGROUP, MAC,EVENT,IMG_PATH)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (t1, t2, t3,mac, str_event, image_name))
            self.db_conn.commit()
            print('\nAfter commit:')

    def insert_key_track(self, t1, t2, t3,mac, event, image_name):
        if self.db_conn:
            cursor = self.db_conn.cursor()
            # db_conn.executescript("""
            # insert into TRACK (TIME,TIMESTEMP,EVENT,POINT_X,POINT_Y,IMG_PATH)
            # values (t, t, event, x, y, image_name);
            # """)
            cursor.execute('''
            INSERT INTO TRACK (TIME,TIMESTEMP, TIMEGROUP,MAC,EVENT,IMG_PATH)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (t1, t2, t3, mac, event, image_name))
            self.db_conn.commit()
            print('\nAfter commit:')


class SqlitePool:
    def __init__(self, db_path='./trackDB.db', max_size=10):
        self.db_path = db_path
        self.pool = deque(maxlen=max_size)
        for _ in range(max_size):
            #self.pool.append(sqlite3.connect(db_path, uri=True, timeout=10, check_same_thread=False))
            client = SqlClient(db_path)
            client.initDB()
            self.pool.append(client)
    
    def get_connection(self):
        if not self.pool:
            #return sqlite3.connect(self.db_path, uri=True, timeout=10, check_same_thread=False)
            client = SqlClient(self.db_path)
            client.initDB()
            return client
        return self.pool.popleft()
    
    def release_connection(self, conn):
        self.pool.append(conn)

# sql_conn = SqlClient()
# sql_conn.initDB()
# sql_conn.insert_click_track(data_day, time_stamp, "XXXXX", "click", 100, 200, "imgXXXXX")
# sql_conn.insert_key_track(data_day, time_stamp, "XXXXX", "keyboard:x", "imgXXXXX")

