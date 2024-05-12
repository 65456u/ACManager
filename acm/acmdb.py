import sqlite3

import bcrypt

from .data import Settings, Invoice, ReportItem
from .sql_queries import *
from .utils import calculate_cost
from .values import invalid_ac_setting, default_ac_setting


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
        query = "SELECT id, password, salt , role FROM users WHERE username = ?"
        values = (username,)
        self.c.execute(query, values)
        user = self.c.fetchone()
        if user is None:
            return 0, 0
        user_id, hashed_password, salt, role = user
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            return True
        # get room_id from rooms
        query = "SELECT id FROM rooms WHERE user_id = ?"
        self.c.execute(query, (user_id,))
        room_id = self.c.fetchone()
        return role, room_id

    def checkin(self, user_id):
        # find a room that isn't busy
        query = "SELECT id, ac_on, temperature, fan_speed, mode FROM rooms WHERE busy = 0"
        self.c.execute(query)
        room = self.c.fetchone()
        if room is None:
            return -1
        room_id, ac_on, temperature, fan_speed, mode = room
        busy = 1
        # get current time
        get_time_query = "SELECT datetime('now')"
        self.c.execute(get_time_query)
        start_time = self.c.fetchone()[0]
        # update the room
        update_room_query = r"""
        UPDATE rooms
        SET busy = ?, user_id = ?, start_time = ?, temperature = ?, fan_speed = ?, mode = ?
        WHERE id = ?"""
        values = (busy, user_id, start_time, temperature, fan_speed, mode, room_id)
        self.c.execute(update_room_query, values)
        # insert user record
        insert_user_record_query = "INSERT INTO user_record (user_id, in_time) VALUES (?, ?)"
        values = (user_id, start_time)
        self.c.execute(insert_user_record_query, values)
        self.conn.commit()
        return room_id

    def get_cost(self, user_id):
        # get start time from user_record
        query = "SELECT in_time FROM user_record WHERE user_id = ?"
        values = (user_id,)
        self.c.execute(query, values)
        in_time = self.c.fetchone()[0]
        # get records from ac_usage_record
        get_records_query = "SELECT start_time, cost FROM ac_usage_record WHERE user_id = ?"
        self.c.execute(get_records_query, values)
        records = self.c.fetchall()
        total_cost = 0
        for record in records:
            start_time, cost = record
            # make sure the record is after the user checkin time
            if start_time >= in_time:
                total_cost += cost
        # get room's current status
        query = "SELECT id, ac_on, start_time, temperature, fan_speed, mode FROM rooms WHERE user_id = ?"
        self.c.execute(query, values)
        room = self.c.fetchone()
        if room is None:
            return -1
        room_id, ac_on, start_time, temperature, fan_speed, mode = room
        # get current time
        get_time_query = "SELECT datetime('now')"
        self.c.execute(get_time_query)
        end_time = self.c.fetchone()[0]
        cost = calculate_cost(start_time, end_time, temperature, fan_speed, mode)
        total_cost += cost
        return total_cost

    def checkout(self, user_id):
        # check the room status
        query = "SELECT busy, ac_on FROM rooms WHERE user_id = ?"
        values = (user_id,)
        self.c.execute(query, values)
        room = self.c.fetchone()
        if room is None or room[0] == 0:
            return -1
        room_id, ac_on = room
        if ac_on == 1:
            # turn off the ac
            self.turn_off_ac(room_id)
        # get the user checkin time
        query = "SELECT start_time FROM rooms WHERE user_id = ?"
        self.c.execute(query, values)
        # get the last record
        start_time = self.c.fetchone()[0]
        # get records from ac_usage_record
        # get_records_query = "SELECT * FROM ac_usage_record WHERE user_id = ?"
        # self.c.execute(get_records_query, values)
        # records = self.c.fetchall()
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
        delete_user_record_query = "DELETE FROM rooms WHERE user_id = ?"
        self.c.execute(delete_user_record_query, values)
        return total_cost, invoices

    def turn_on_ac(self, room_id):
        # check the room status
        query = "SELECT busy, ac_on, temperature, fan_speed, mode FROM rooms WHERE id = ?"
        values = (room_id,)
        self.c.execute(query, values)
        room = self.c.fetchone()
        if room is None or room[0] == 0:
            return -1
        busy, ac_on, user_id, start_time, temperature, fan_speed, mode = room
        if ac_on == 1:
            return -2
        settings = Settings(temperature = temperature, fan_speed = fan_speed, mode = mode)
        # get current time
        get_time_query = "SELECT datetime('now')"
        self.c.execute(get_time_query)
        start_time = self.c.fetchone()[0]
        # update the room
        update_room_query = "UPDATE rooms SET ac_on = 1 WHERE id = ?"
        values = (room_id,)
        self.c.execute(update_room_query, values)
        self.conn.commit()
        return 0, settings

    def turn_off_ac(self, room_id):
        settings = invalid_ac_setting
        # make sure the room is busy
        query = "SELECT busy, ac_on ,user_id,start_time,temperature,fan_speed,mode FROM rooms WHERE id = ?"
        values = (room_id,)
        self.c.execute(query, values)
        room = self.c.fetchone()
        if room is None or room[0] == 0:
            return -1, settings
        busy, ac_on, user_id, start_time, temperature, fan_speed, mode = room
        if ac_on == 0:
            return -2, settings
        # get current time
        get_time_query = "SELECT datetime('now')"
        self.c.execute(get_time_query)
        end_time = self.c.fetchone()[0]
        # calculate the cost
        cost = calculate_cost(start_time, end_time, temperature, fan_speed, mode)
        # insert the record
        self.insert_ac_usage_record(user_id, room_id, start_time, end_time, temperature, fan_speed, mode, cost)
        # update the room
        update_room_query = "UPDATE rooms SET ac_on = 0 WHERE id = ?"
        values = (room_id,)
        self.c.execute(update_room_query, values)
        self.conn.commit()
        settings = Settings(temperature = temperature, fan_speed = fan_speed, mode = mode)
        return 0, settings

    def set_ac(self, room_id, settings: Settings):
        # check the room status
        query = "SELECT busy, ac_on FROM rooms WHERE id = ?"
        values = (room_id,)
        self.c.execute(query, values)
        room = self.c.fetchone()
        if room is None or room[0] == 0:
            return -1, invalid_ac_setting
        busy, ac_on = room
        if ac_on == 0:
            return -2, invalid_ac_setting
        # get current time
        get_time_query = "SELECT datetime('now')"
        self.c.execute(get_time_query)
        start_time = self.c.fetchone()[0]
        # update the room
        update_room_query = "UPDATE rooms SET temperature = ?, fan_speed = ?, mode = ? WHERE id = ?"
        values = (settings.temperature, settings.fan_speed, settings.mode, room_id)
        self.c.execute(update_room_query, values)
        self.conn.commit()
        return 0, settings

    def check_status(self, room_id):
        query = r"""SELECT busy, ac_on, user_id, start_time, temperature,fan_speed, mode FROM rooms WHERE id = ?"""
        self.c.execute(query, (room_id,))
        room = self.c.fetchone()
        if room is None:
            return None
        busy, ac_on, user_id, start_time, temperature, fan_speed, mode = room
        settings = Settings(temperature = temperature, fan_speed = fan_speed, mode = mode)
        return busy, ac_on, user_id, start_time, settings

    # 查询统计报表，统计房间的使用详单
    def generate_report(self, room_id):
        # # 查询房间的空调使用记录，并计算总消费
        # query = r"""
        # SELECT SUM(cost) FROM ac_usage_record WHERE room_id = ?
        # """
        # self.c.execute(query, (room_id,))
        # total_cost = self.c.fetchone()[0]
        # 查询房间的空调使用记录
        query = r"""SELECT * FROM ac_usage_record WHERE room_id = ?"""
        self.c.execute(query, (room_id,))
        usage_records = self.c.fetchall()
        report_items = []
        for record in usage_records:
            user_id, room_id, start_time, end_time, temperature, fan_speed, mode, cost = record
            settings = Settings(temperature = temperature, fan_speed = fan_speed, mode = mode)
            report_item = ReportItem(room_id = room_id, user_id = user_id, start_time = start_time, end_time = end_time,
                                     cost = cost, settings = settings)
            report_items.append(report_item)
        return report_items

    # 提供消费账单和详单
    def generate_bill(self, user_id):
        query = r"""
        SELECT room_id, start_time, end_time, temperature, fan_speed, mode, cost
        FROM ac_usage_record
        WHERE user_id = ?"""
        self.c.execute(query, (user_id,))
        bill = self.c.fetchall()
        # get in time from user_record
        query = "SELECT in_time FROM user_record WHERE user_id = ?"
        values = (user_id,)
        self.c.execute(query, values)
        in_time = self.c.fetchone()[0]
        # only return records after the user checkin time
        invoices = []
        total_cost = 0
        for bill_item in bill:
            room_id, start_time, end_time, temperature, fan_speed, mode, cost = bill_item
            if start_time < in_time:
                continue
            settings = Settings(temperature = temperature, fan_speed = fan_speed, mode = mode)
            invoice = Invoice(room_id = room_id, start_time = start_time, end_time = end_time, settings = settings,
                              cost = cost)
            invoices.append(invoice)
            total_cost += cost
        return total_cost, invoices

    # 插入用户信息
    def insert_user(self, username, password, phone):
        insert_user_query = r"""INSERT INTO users (username, password, phone) VALUES (?, ?, ?)"""
        self.c.execute(insert_user_query, (username, password, phone))
        self.conn.commit()

    # 插入房间信息
    def insert_room(self, busy, ac_on, user_id, start_time, temperature, fan_speed, mode):
        insert_room_query = r"""
        INSERT INTO rooms (busy, ac_on, user_id, start_time, temperature, fan_speed, mode)
        VALUES (?, ?, ?, ?, ?, ?, ?)"""
        self.c.execute(insert_room_query, (busy, ac_on, user_id, start_time, temperature, fan_speed, mode))
        self.conn.commit()

    # 插入空调使用记录表
    def insert_ac_usage_record(self, user_id, room_id, start_time, end_time, temperature, fan_speed, mode, cost):
        insert_ac_usage_record_query = r"""
        INSERT INTO ac_usage_record
        (user_id, room_id, start_time, end_time, temperature, fan_speed, mode, cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        self.c.execute(insert_ac_usage_record_query,
                       (user_id, room_id, start_time, end_time, temperature, fan_speed, mode, cost))
        self.conn.commit()

    # 插入房间占用信息
    # def insert_room_occupation(self, room_id, user_id):
    #     insert_room_occupation_query = r"""
    #     INSERT INTO room_occupation (room_id, user_id) VALUES (?, ?)
    #     """
    #     self.c.execute(insert_room_occupation_query, (room_id, user_id))
    #     self.conn.commit()

    # 插入空调状态信息
    # def insert_ac_status(self, room_id, start_time, temperature, fan_speed, mode):
    #     insert_ac_status_query = r"""
    #     INSERT INTO ac_status (room_id, start_time, temperature, fan_speed, mode)
    #     VALUES (?, ?, ?, ?, ?);
    #     """
    #     self.c.execute(insert_ac_status_query, (room_id, start_time, temperature, fan_speed, mode))
    #     self.conn.commit()

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
        # self.c.execute(create_ac_status_table_query)
        self.c.execute(create_user_record_query)
        self.conn.commit()

    def add_rooms(self, count):
        for i in range(count):
            self.insert_room(0, 0, -1, "", default_ac_setting.temperature, default_ac_setting.fan_speed,
                             default_ac_setting.mode)
