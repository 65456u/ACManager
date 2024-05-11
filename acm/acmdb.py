import sqlite3

import bcrypt

from .data import Settings
from .sql_queries import *


class ACMDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('acm.db')
        # set encoding to utf-8
        self.c = self.conn.cursor()
        self._create_tables()

    def register_user(self, username, phone, password):
        # Generate a new salt
        salt = bcrypt.gensalt()

        # Hash the password with the generated salt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

        # Insert user into the database and get the user id
        insert_query = "INSERT INTO users (username, password, salt, phone) VALUES (?, ?, ?, ?)"
        values = (username, hashed_password.decode('utf-8'), salt.decode('utf-8'), phone)

        try:
            self.c.execute(insert_query, values)
            user_id = self.c.lastrowid
            self.conn.commit()
            return user_id
        except sqlite3.Error as e:
            print("Error registering user:", e)
            return None

    def login(self, username, password):
        query = "SELECT id, password, salt FROM users WHERE username = ?"
        values = (username,)
        self.c.execute(query, values)
        user = self.c.fetchone()
        if user is None:
            return None
        user_id, hashed_password, salt = user
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            return True
        return False

    def checkin(self, user_id):
        # find a room that is not busy
        query = "SELECT id FROM rooms WHERE busy = 0"
        self.c.execute(query)
        room = self.c.fetchone()
        if room is None:
            return None
        room_id = room[0]
        # set the room to busy
        update_query = "UPDATE rooms SET busy = 1 WHERE id = ?"
        values = (room_id,)
        self.c.execute(update_query, values)
        self.conn.commit()
        # insert the room occupation record
        insert_query = "INSERT INTO room_occupation (room_id, user_id) VALUES (?, ?)"
        values = (room_id, user_id)
        self.c.execute(insert_query, values)
        self.conn.commit()
        return room_id

    def turn_on_ac(self, room_id):
        # make sure the room is busy
        query = "SELECT busy FROM rooms WHERE id = ?"
        values = (room_id,)
        self.c.execute(query, values)
        room = self.c.fetchone()
        if room is None or room[0] == 0:
            return -1
        # check it there exists a record for the room
        query = "SELECT * FROM ac_status WHERE room_id = ?"
        self.c.execute(query, values)
        record = self.c.fetchone()
        # alter the record if there exists one, otherwise insert a new record

    def turn_off_ac(self, room_id):
        pass

    def set_ac(self, room_id, settings: Settings):
        pass

    def checkout(self, user_id):
        pass

    def _create_tables(self):
        self.c.execute(create_user_table_query)
        self.c.execute(create_room_table_query)
        self.c.execute(create_ac_usage_record_table_query)
        self.c.execute(create_room_occupation_table_query)
        self.c.execute(create_ac_status_table_query)
        self.conn.commit()
