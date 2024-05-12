import sqlite3


class ACMDatabase:
    def __init__(self, path = 'acm.db'):
        self.path = path

    def get_connection(self):
        return sqlite3.connect(self.path, check_same_thread = False)
