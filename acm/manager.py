from .acmdb import ACMDatabase


class Manager:
    def __init__(self):
        self.db = ACMDatabase()
