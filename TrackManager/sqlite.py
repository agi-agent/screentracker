#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  @Time    : 2025-01-17 21:30
#  @Author  : yanmin
#  @Site    :
#  @File    : .py
#  @Software: vscode
import os
import time
import sqlite3
db_name = './trackDB.db'
schema_filename = './user.sql'

class SqlClient:
    db_filename = './trackDB.db'
    db_conn = None
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

# current_time = time.time()
# local_time = time.localtime(current_time)
# data_head = time.strftime("%Y-%m-%d-%H:%M:%S", local_time)
# data_secs = (current_time - int(current_time)) * 1000
# time_stamp = "%s:%03d" % (data_head, data_secs)
# data_day = time.strftime("%Y-%m-%d", local_time)

# sql_conn = SqlClient()
# sql_conn.initDB()
# sql_conn.insert_click_track(data_day, time_stamp, "XXXXX", "click", 100, 200, "imgXXXXX")
# sql_conn.insert_key_track(data_day, time_stamp, "XXXXX", "keyboard:x", "imgXXXXX")

