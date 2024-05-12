import sqlite3

import bcrypt

from .acmdb import ACMDatabase
from .data import Settings, Invoice, ReportItem
from .sql_queries import *
from .utils import calculate_cost
from .values import invalid_ac_setting, default_ac_setting

MIN_ROOM_COUNT = 50


class Manager:
    def __init__(self, room_count=100):
        self.db = ACMDatabase()
        self.conn = self.db.get_connection()
        self._create_tables()
        self.init_rooms()

    def register_user(self, username, phone, password):
        c = self.conn.cursor()
        # Generate a new salt
        salt = bcrypt.gensalt()
        # Hash the password with the generated salt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        # Insert user into the database and get the user id
        insert_query = "INSERT INTO users (username, password, salt, phone,role) VALUES (?, ?, ?, ?,?)"
        role = 1
        values = (username, hashed_password.decode('utf-8'), salt.decode('utf-8'), phone, role)
        try:
            c.execute(insert_query, values)
            user_id = c.lastrowid
            self.conn.commit()
            return user_id
        except sqlite3.Error as e:
            print("Error registering user:", e)
            return -1

    def login(self, username, password):
        c = self.conn.cursor()
        query = "SELECT id, password, salt , role FROM users WHERE username = ?"
        values = (username,)
        c.execute(query, values)
        user = c.fetchone()
        print(user)
        if user is None:
            return 0, 0
        user_id, hashed_password, salt, role = user
        if not bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            return 0, 0
        # get room_id from rooms
        query = "SELECT id FROM rooms WHERE user_id = ?"
        c.execute(query, (user_id,))
        room_id = c.fetchone()
        if room_id is None:
            room_id = -1
        else:
            room_id = room_id[0]
        return role, room_id, user_id

    def checkin(self, user_id):
        c = self.conn.cursor()
        # check if the user exists
        query = "SELECT id FROM users WHERE id = ?"
        c.execute(query, (user_id,))
        user = c.fetchone()
        if user is None:
            return -3
        # check if user already checked in from user_record
        query = "SELECT user_id FROM rooms WHERE user_id = ?"
        c.execute(query, (user_id,))
        room = c.fetchone()
        if room is not None:
            return -2
        # find a room that isn't busy
        query = "SELECT id, ac_on, temperature, fan_speed, mode FROM rooms WHERE busy = 0"
        c.execute(query)
        room = c.fetchone()
        if room is None:
            return -1
        room_id, ac_on, temperature, fan_speed, mode = room
        busy = 1
        # get current time
        get_time_query = "SELECT datetime('now')"
        c.execute(get_time_query)
        start_time = c.fetchone()[0]
        # update the room
        update_room_query = r"""
        UPDATE rooms
        SET busy = ?, user_id = ?, start_time = ?, temperature = ?, fan_speed = ?, mode = ?
        WHERE id = ?"""
        values = (busy, user_id, start_time, temperature, fan_speed, mode, room_id)
        c.execute(update_room_query, values)
        # insert user record
        insert_user_record_query = "INSERT INTO user_record (user_id, in_time) VALUES (?, ?)"
        values = (user_id, start_time)
        c.execute(insert_user_record_query, values)
        self.conn.commit()
        return room_id

    def get_cost(self, user_id):
        c = self.conn.cursor()
        # get start time from user_record
        query = "SELECT in_time FROM user_record WHERE user_id = ?"
        values = (user_id,)
        c.execute(query, values)
        in_time = c.fetchone()[0]
        # get records from ac_usage_record
        get_records_query = "SELECT start_time, cost FROM ac_usage_record WHERE user_id = ?"
        c.execute(get_records_query, values)
        records = c.fetchall()
        total_cost = 0
        for record in records:
            start_time, cost = record
            # make sure the record is after the user checkin time
            if start_time >= in_time:
                total_cost += cost
        # get room's current status
        query = "SELECT id, ac_on, start_time, temperature, fan_speed, mode FROM rooms WHERE user_id = ?"
        c.execute(query, values)
        room = c.fetchone()
        if room is None:
            return -1
        room_id, ac_on, start_time, temperature, fan_speed, mode = room
        # get current time
        get_time_query = "SELECT datetime('now')"
        c.execute(get_time_query)
        end_time = c.fetchone()[0]
        if ac_on == 1:
            cost = calculate_cost(start_time, end_time, temperature, fan_speed, mode)
            total_cost += cost
        return total_cost

    def checkout(self, user_id):
        c = self.conn.cursor()
        # check the room status
        query = "SELECT busy, ac_on FROM rooms WHERE user_id = ?"
        values = (user_id,)
        c.execute(query, values)
        room = c.fetchone()
        if room is None or room[0] == 0:
            return -1
        room_id, ac_on = room
        if ac_on == 1:
            # turn off the ac
            self.turn_off_ac(room_id)
        # get the user checkin time
        query = "SELECT start_time FROM rooms WHERE user_id = ?"
        c.execute(query, values)
        # get the last record
        # start_time = c.fetchone()[0]
        # get records from ac_usage_record
        # get_records_query = "SELECT * FROM ac_usage_record WHERE user_id = ?"
        # c.execute(get_records_query, values)
        # records = c.fetchall()
        # invoices = []
        # total_cost = 0
        # for record in records:
        #     user_id, room_id, start_time, end_time, temperature, fan_speed, mode, cost = record
        #     total_cost += cost
        #     settings = Settings(temperature = temperature, fan_speed = fan_speed, mode = mode)
        #     invoices.append(
        #         Invoice(room_id = room_id, start_time = start_time, end_time = end_time, settings = settings,
        #                 cost = cost))
        # delete user record
        total_cost, invoices = self.generate_bill(user_id)
        delete_user_record_query = "DELETE FROM user_record WHERE user_id = ?"
        c.execute(delete_user_record_query, values)

        # update the room
        update_room_query = "UPDATE rooms SET busy = 0, user_id = -1, start_time = '', ac_on = 0 WHERE user_id = ?"
        c.execute(update_room_query, values)
        self.conn.commit()
        return total_cost, invoices

    def turn_on_ac(self, room_id):
        c = self.conn.cursor()
        # check the room status
        query = "SELECT busy, ac_on, start_time, temperature, fan_speed, mode FROM rooms WHERE id = ?"
        values = (room_id,)
        c.execute(query, values)
        room = c.fetchone()
        if room is None or room[0] == 0:
            return -1, invalid_ac_setting
        busy, ac_on, start_time, temperature, fan_speed, mode = room
        if ac_on == 1:
            return -2, invalid_ac_setting
        settings = Settings(temperature=temperature, fan_speed=fan_speed, mode=mode)
        # get current time
        get_time_query = "SELECT datetime('now')"
        c.execute(get_time_query)
        start_time = c.fetchone()[0]
        # update the room
        update_room_query = "UPDATE rooms SET ac_on = 1, start_time = ? WHERE id = ?"
        values = (start_time, room_id)
        c.execute(update_room_query, values)
        self.conn.commit()
        return 0, settings

    def turn_off_ac(self, room_id):
        c = self.conn.cursor()
        settings = invalid_ac_setting
        # make sure the room is busy
        query = "SELECT busy, ac_on ,user_id,start_time,temperature,fan_speed,mode FROM rooms WHERE id = ?"
        values = (room_id,)
        c.execute(query, values)
        room = c.fetchone()
        if room is None or room[0] == 0:
            return -1, settings
        busy, ac_on, user_id, start_time, temperature, fan_speed, mode = room
        if ac_on == 0:
            return -2, settings
        # get current time
        get_time_query = "SELECT datetime('now')"
        c.execute(get_time_query)
        end_time = c.fetchone()[0]
        print(start_time, end_time, temperature, fan_speed, mode)
        # calculate the cost
        cost = calculate_cost(start_time, end_time, temperature, fan_speed, mode)
        # insert the record
        self.insert_ac_usage_record(user_id, room_id, start_time, end_time, temperature, fan_speed, mode, cost)
        # update the room
        update_room_query = "UPDATE rooms SET ac_on = 0 WHERE id = ?"
        values = (room_id,)
        c.execute(update_room_query, values)
        self.conn.commit()
        settings = Settings(temperature=temperature, fan_speed=fan_speed, mode=mode)
        return 0, settings

    def set_ac(self, room_id, settings: Settings):
        c = self.conn.cursor()
        # check the room status
        query = "SELECT busy, ac_on FROM rooms WHERE id = ?"
        values = (room_id,)
        c.execute(query, values)
        room = c.fetchone()
        if room is None or room[0] == 0:
            return -1, invalid_ac_setting
        busy, ac_on = room
        if ac_on == 0:
            return -2, invalid_ac_setting
        # get current time
        get_time_query = "SELECT datetime('now')"
        c.execute(get_time_query)
        current_time = c.fetchone()[0]
        # get the previous setting
        query = "SELECT id, user_id,start_time, temperature, fan_speed, mode FROM rooms WHERE id = ?"
        c.execute(query, values)
        room = c.fetchone()
        if room is None:
            return -3, invalid_ac_setting
        room_id, user_id, start_time, temperature, fan_speed, mode = room
        # insert the record
        self.insert_ac_usage_record(user_id, room_id, start_time, current_time, temperature, fan_speed, mode,
                                    calculate_cost(start_time, current_time, temperature, fan_speed, mode))
        # update the room
        update_room_query = "UPDATE rooms SET temperature = ?, fan_speed = ?, mode = ? WHERE id = ?"
        values = (settings.temperature, settings.fan_speed, settings.mode, room_id)
        c.execute(update_room_query, values)

        self.conn.commit()
        return 0, settings

    def check_status(self, room_id):
        c = self.conn.cursor()
        query = r"""SELECT busy, ac_on, user_id, start_time, temperature,fan_speed, mode FROM rooms WHERE id = ?"""
        print(room_id)
        values = (room_id,)
        c.execute(query, values)
        room = c.fetchone()
        print(room)
        if room is None:
            return None
        busy, ac_on, user_id, start_time, temperature, fan_speed, mode = room
        settings = Settings(temperature=temperature, fan_speed=fan_speed, mode=mode)
        return busy, ac_on, user_id, start_time, settings

    # 查询统计报表，统计房间的使用详单
    def generate_report(self):
        c = self.conn.cursor()
        # # 查询房间的空调使用记录，并计算总消费
        # query = r"""
        # SELECT SUM(cost) FROM ac_usage_record WHERE room_id = ?
        # """
        # c.execute(query, (room_id,))
        # total_cost = c.fetchone()[0]
        # 查询房间的空调使用记录
        query = r"""
        SELECT user_id, room_id, start_time, end_time, temperature, fan_speed, mode, cost
        FROM ac_usage_record"""
        c.execute(query)
        usage_records = c.fetchall()
        report_items = []
        for record in usage_records:
            user_id, room_id, start_time, end_time, temperature, fan_speed, mode, cost = record
            settings = Settings(temperature=temperature, fan_speed=fan_speed, mode=mode)
            report_item = ReportItem(room_id=room_id, user_id=user_id, start_time=start_time, end_time=end_time,
                                     cost=cost, settings=settings)
            report_items.append(report_item)
        return report_items

    # 提供消费账单和详单
    def generate_bill(self, user_id):
        c = self.conn.cursor()
        query = r"""
        SELECT room_id, start_time, end_time, temperature, fan_speed, mode, cost
        FROM ac_usage_record
        WHERE user_id = ?"""
        c.execute(query, (user_id,))
        bill = c.fetchall()

        everything = "SELECT * FROM user_record"
        c.execute(everything)
        print(c.fetchall())

        # get in time from user_record
        query = "SELECT in_time FROM user_record WHERE user_id = ?"
        print(user_id)

        values = (user_id,)
        c.execute(query, values)
        in_time = c.fetchone()
        if in_time is None:
            return 0, []
        in_time = in_time[0]
        print(in_time)
        # only return records after the user checkin time
        invoices = []
        total_cost = 0
        for bill_item in bill:
            room_id, start_time, end_time, temperature, fan_speed, mode, cost = bill_item
            if start_time < in_time:
                continue
            settings = Settings(temperature=temperature, fan_speed=fan_speed, mode=mode)
            invoice = Invoice(room_id=room_id, start_time=start_time, end_time=end_time, settings=settings,
                              cost=cost)
            invoices.append(invoice)
            total_cost += cost
        return total_cost, invoices

    # 插入用户信息
    def insert_user(self, username, password, phone):
        c = self.conn.cursor()
        insert_user_query = r"""INSERT INTO users (username, password, phone) VALUES (?, ?, ?)"""
        c.execute(insert_user_query, (username, password, phone))
        self.conn.commit()

    # 插入房间信息
    def insert_room(self, busy, ac_on, user_id, start_time, temperature, fan_speed, mode):
        c = self.conn.cursor()
        insert_room_query = r"""
        INSERT INTO rooms (busy, ac_on, user_id, start_time, temperature, fan_speed, mode)
        VALUES (?, ?, ?, ?, ?, ?, ?)"""
        c.execute(insert_room_query, (busy, ac_on, user_id, start_time, temperature, fan_speed, mode))
        self.conn.commit()

    # 插入空调使用记录表
    def insert_ac_usage_record(self, user_id, room_id, start_time, end_time, temperature, fan_speed, mode, cost):
        c = self.conn.cursor()
        insert_ac_usage_record_query = r"""
        INSERT INTO ac_usage_record
        (user_id, room_id, start_time, end_time, temperature, fan_speed, mode, cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        c.execute(insert_ac_usage_record_query,
                  (user_id, room_id, start_time, end_time, temperature, fan_speed, mode, cost))
        self.conn.commit()

    # 插入房间占用信息
    # def insert_room_occupation(self, room_id, user_id):
    #     insert_room_occupation_query = r"""
    #     INSERT INTO room_occupation (room_id, user_id) VALUES (?, ?)
    #     """
    #     c.execute(insert_room_occupation_query, (room_id, user_id))
    #     self.conn.commit()

    # 插入空调状态信息
    # def insert_ac_status(self, room_id, start_time, temperature, fan_speed, mode):
    #     insert_ac_status_query = r"""
    #     INSERT INTO ac_status (room_id, start_time, temperature, fan_speed, mode)
    #     VALUES (?, ?, ?, ?, ?);
    #     """
    #     c.execute(insert_ac_status_query, (room_id, start_time, temperature, fan_speed, mode))
    #     self.conn.commit()

    '''
    # 输出当前全部空调状态
    def fetch_all_ac_statuses(self):
        query = "SELECT * FROM ac_status"
        c.execute(query)
        print("所有空调状态如下:\n")
        print(c.fetchall())

    # 输出当前全部空调状态
    def fetch_all_ac_usage_record(self):
        query = "SELECT * FROM ac_usage_record"
        c.execute(query)
        print("所有空调记录如下:\n")
        print(c.fetchall())
    '''

    def _create_tables(self):
        c = self.conn.cursor()
        c.execute(create_user_table_query)
        c.execute(create_room_table_query)
        c.execute(create_ac_usage_record_table_query)
        # c.execute(create_ac_status_table_query)
        c.execute(create_user_record_query)
        self.conn.commit()

    def add_rooms(self, count):
        for i in range(count):
            self.insert_room(0, 0, -1, "", default_ac_setting.temperature, default_ac_setting.fan_speed,
                             default_ac_setting.mode)

    def init_rooms(self):
        # check if the room count is under the minimum
        c = self.conn.cursor()
        query = "SELECT COUNT(*) FROM rooms"
        c.execute(query)
        room_count = c.fetchone()[0]
        if room_count < MIN_ROOM_COUNT:
            self.add_rooms(MIN_ROOM_COUNT - room_count)

    def get_user_id_by_name(self, username):
        c = self.conn.cursor()
        query = "SELECT id FROM users WHERE username = ?"
        c.execute(query, (username,))
        user_id = c.fetchone()
        if user_id is None:
            return -1
        return user_id[0]
