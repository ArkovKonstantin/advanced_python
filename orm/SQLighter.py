import sqlite3


class SQLighter:
    def __init__(self, db_name):
        self._connection = sqlite3.connect(db_name)
        self._db_field = {"IntField": "INTEGER", "StringField": "TEXT"}
        self.cursor = self._connection.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._connection.close()


