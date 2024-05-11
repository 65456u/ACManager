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

    # 查看空调状态
    def check_status(self, room_id):
        query = r"""
        SELECT * FROM ac_status WHERE room_id = ?
        """
        self.c.execute(query, (room_id,))
        return self.c.fetchall()

    # 查询统计报表，统计房间的使用详单
    def generate_report(self, room_id):
        # 查询房间的空调使用记录，并计算总消费
        query = r"""
        SELECT SUM(cost) FROM ac_usage_record WHERE room_id = ?
        """
        self.c.execute(query, (room_id,))
        total_cost = self.c.fetchone()[0]
        # 查询房间的空调使用记录
        query = r"""
        SELECT * FROM ac_usage_record WHERE room_id = ?
        """
        self.c.execute(query, (room_id,))
        report = self.c.fetchall()
        return total_cost, report

    # 提供消费账单和详单
    def generate_bill(self, user_id):
        query = r"""
        SELECT SUM(cost) FROM ac_usage_record WHERE user_id = ?
        """
        self.c.execute(query, (user_id,))
        total_cost = self.c.fetchone()[0]
        query = r"""
        SELECT * FROM ac_usage_record WHERE user_id = ?
        """
        self.c.execute(query, (user_id,))
        bill = self.c.fetchall()
        return total_cost, bill

    # 插入用户信息
    def insert_user(self, username, password, phone):
        insert_user_query = r"""
        INSERT INTO users (username, password, phone) VALUES (?, ?, ?)
        """
        self.c.execute(insert_user_query, (username, password, phone))
        self.conn.commit()

    # 插入房间信息
    def insert_room(self, busy):
        insert_room_query = r"""
        INSERT INTO rooms (busy) VALUES (?)
        """
        self.c.execute(insert_room_query, (busy,))
        self.conn.commit()

    # 插入空调使用记录表
    def insert_ac_usage_record(self, user_id, room_id, start_time, end_time, temperature, fan_speed, mode, cost):
        insert_ac_usage_record_query = r"""
        INSERT INTO ac_usage_record (user_id, room_id, start_time, end_time, temperature, fan_speed, mode, cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.c.execute(insert_ac_usage_record_query,
                       (user_id, room_id, start_time, end_time, temperature, fan_speed, mode, cost))
        self.conn.commit()

    # 插入房间占用信息
    def insert_room_occupation(self, room_id, user_id):
        insert_room_occupation_query = r"""
        INSERT INTO room_occupation (room_id, user_id) VALUES (?, ?)
        """
        self.c.execute(insert_room_occupation_query, (room_id, user_id))
        self.conn.commit()

    # 插入空调状态信息
    def insert_ac_status(self, room_id, start_time, temperature, fan_speed, mode):
        insert_ac_status_query = r"""
        INSERT INTO ac_status (room_id, start_time, temperature, fan_speed, mode)
        VALUES (?, ?, ?, ?, ?);
        """
        self.c.execute(insert_ac_status_query, (room_id, start_time, temperature, fan_speed, mode))
        self.conn.commit()

    '''
    # 输出当前全部空调状态
    def fetch_all_ac_statuses(self):
        query = "SELECT * FROM ac_status"
        self.c.execute(query)
        print("所有空调状态如下:\n")
        print(self.c.fetchall())

    # 输出当前全部空调状态
    def fetch_all_ac_usage_record(self):
        query = "SELECT * FROM ac_usage_record"
        self.c.execute(query)
        print("所有空调记录如下:\n")
        print(self.c.fetchall())
    '''

    def _create_tables(self):
        self.c.execute(create_user_table_query)
        self.c.execute(create_room_table_query)
        self.c.execute(create_ac_usage_record_table_query)
        self.c.execute(create_room_occupation_table_query)
        self.c.execute(create_ac_status_table_query)
        self.conn.commit()
