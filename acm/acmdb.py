import sqlite3

from settings import Settings


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
            cost INTEGER,
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
