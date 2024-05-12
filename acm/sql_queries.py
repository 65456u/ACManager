create_user_table_query = r"""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        phone TEXT UNIQUE,
        salt TEXT,
        role INTEGER
    );
    """
# 1 for customer, 2 for staff, 3 for administrator
create_room_table_query = r"""
    CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        busy INTEGER,
        ac_on INTEGER,
        user_id INTEGER,
        start_time TEXT,
        temperature INTEGER,
        fan_speed TEXT,
        mode TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)  
    );
    """
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
        cost REAL,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(room_id) REFERENCES rooms(id)
    );
    """
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

create_user_record_query = r"""
    CREATE TABLE IF NOT EXISTS user_record(
        user_id INTEGER,
        in_time TEXT,
        out_time TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        PRIMARY KEY(user_id, in_time)
    );
"""
