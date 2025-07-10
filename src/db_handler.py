import sqlite3

class DatabaseHandler:
    def __init__(self, db_path: str = "{YOUR_PATH}"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def cursor(self):
        return self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def rollback(self):
        self.conn.rollback()