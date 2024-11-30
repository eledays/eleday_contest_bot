import sqlite3
from datetime import datetime, timedelta


class Databaser:

    def __init__(self, filename='app.db'):
        self.conn = sqlite3.connect(filename, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Contests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR NOT NULL,
                desc TEXT NOT NULL,
                rules TEXT NOT NULL, 
                one_solution BOOLEAN DEFAULT(TRUE) NOT NULL,
                length_check BOOLEAN DEFAULT(TRUE) NOT NULL,
                start_datetime DATETIME,
                end_datetime DATETIME
            )''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Solutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id INTEGER NOT NULL,
                contest_id INTEGER NOT NULL,
                code TEXT NOT NULL, 
                length INTEGER NOT NULL,
                datetime DATETIME NOT NULL
            )''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY,
                total_solutions_count INTEGER DEFAULT 0,
                wins_count INTEGER DEFAULT 0
            )''')
        
        self.conn.commit()

    def create_contest(
            self, name: str, desc : str, 
            rules: str, one_solution: bool = True, 
            length_check: bool = True, 
            start_datetime: datetime = None, 
            end_datetime: datetime = None):

        with self.conn:
            self.cursor.execute('''
                INSERT INTO Contests (name, desc, rules, one_solution, length_check, start_datetime, end_datetime)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, desc, rules, one_solution, length_check, start_datetime, end_datetime))

        return self.cursor.lastrowid

    def start_contest(self, id):
        # r = self.cursor.execute('''SELECT start_datetime FROM Contests WHERE id = ?''', (id,)).fetchone()
        # if r is not None and dict(r)['start_datetime'] is not None and dict(r)['start_datetime'] < datetime.now():
        #     raise Exception('Конкурс уже идёт')
        #TODO
            
        with self.conn:
            self.cursor.execute('''
                UPDATE Contests
                SET start_datetime = ?
                WHERE id = ? AND (start_datetime < ? OR start_datetime IS NULL)
            ''', (datetime.now(), id, datetime.now()))

    def end_contest(self, id):
        with self.conn:
            self.cursor.execute('''
                UPDATE Contests
                SET end_datetime = ?
                WHERE id = ? AND end_datetime IS NULL
            ''', (datetime.now(), id))

    def get_contest(self, id):
        self.cursor.execute('''
            SELECT * FROM Contests
            WHERE id = ?
        ''', (id,))
        r = self.cursor.fetchone()

        if r is None:
            return None

        r = dict(r)
        r['start_datetime'] = datetime.fromisoformat(r['start_datetime']) if r['start_datetime'] is not None else None
        r['end_datetime'] = datetime.fromisoformat(r['end_datetime']) if r['end_datetime'] is not None else None
        return r
    
    def get_contest_status(self, id):
        """Получить статус конкурса (запущен или нет)"""

        r = self.get_contest(id)

        if r is None:
            return None, None

        if r['start_datetime'] is None or r['start_datetime'] > datetime.now():
            return False, 'future'
        
        if r['start_datetime'] is not None and r['start_datetime'] < datetime.now() and (r['end_datetime'] is not None and r['end_datetime'] < datetime.now()):
            return False, 'past'
        
        return True, None

    def close(self):
        self.conn.close()


if __name__ == '__main__':
    db = Databaser()
    # print(db.create_contest(name='test', desc='test', rules='test', start_datetime=datetime.now() + timedelta(days=3)))
    print(dict(db.get_contest(1)))
