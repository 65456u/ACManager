from .acmdb import ACMDatabase


class Manager:
    def __init__(self, room_count = 100):
        self.db = ACMDatabase()
