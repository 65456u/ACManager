import sqlite3

from .data import Settings


class ACMDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('acm.db')
        # set encoding to utf-8
        self.c = self.conn.cursor()
        self._create_tables()

    def register_user(self, username, password):
        pass

    def checkin(self, user_id):
        pass

    def turn_on_ac(self, room_id):
        pass

    def turn_off_ac(self, room_id):
        pass

    def set_ac(self, room_id, settings: Settings):
        pass

    def checkout(self, user_id):
        pass

    def _create_tables(self):
        create_user_table_query = r"""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            phone TEXT
        );
        """
        self.c.execute(create_user_table_query)
        # delete room_table
        delete_room_table_query = r"""
        DROP TABLE IF EXISTS rooms;
        """
        create_room_table_query = r"""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            busy INTEGER
        );
        """
        self.c.execute(delete_room_table_query)
        self.c.execute(create_room_table_query)
        create_ac_usage_record_table_query = r"""
        CREATE TABLE IF NOT EXISTS ac_usage_record(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            room_id INTEGER,
            start_time TEXT,
            end_time TEXT,
            temperature INTEGER,
            fan_speed TEXT,
            mode TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(room_id) REFERENCES rooms(id)
        );
        """
        self.c.execute(create_ac_usage_record_table_query)
        create_room_occuption_table_query = r"""
        CREATE TABLE IF NOT EXISTS room_occupation(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER,
            user_id INTEGER,
            FOREIGN KEY(room_id) REFERENCES rooms(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
        self.c.execute(create_room_occuption_table_query)
        create_ac_status_table_query = r"""
        CREATE TABLE IF NOT EXISTS ac_status(
            room_id INTEGER,
            start_time TEXT,
            temperature INTEGER,
            fan_speed TEXT,
            mode TEXT,
            FOREIGN KEY (room_id) REFERENCES rooms(id),
            PRIMARY KEY(room_id, start_time)
        );
        """
        self.c.execute(create_ac_status_table_query)
        self.conn.commit()
