import sqlite3
import sys
from urllib.request import urlopen
from pathlib import Path
from sqlite3 import Error
import matplotlib.pyplot as plt
import os
from datetime import date


class MySqliteDb:
    def __init__(self):
        try:
            self._db_connection = sqlite3.connect(
                str(Path().absolute()) + r"\DB\pyGieldaDB.db")
            self._db_cursor = self._db_connection.cursor()
        except Exception as error:
            print(error)
        else:
            print('Wersja utworzonej bazy SQLite3: ' + sqlite3.version)

    def query(self, query, parameters=()):
        try:
            result = self._db_cursor.execute(query, parameters)
        except Exception as error:
            print(f'Error executing query"{query}", error: {error}')
        else:
            return result

    def table_in_db(self, name):
        table_names = self.query(
            "SELECT name FROM sqlite_master WHERE type='table';")
        table_names = [x[0] for x in table_names.fetchall()]
        print(f"Szukana tabela: {name}, Lista tabel: {table_names}")
        return name in table_names

    def create_day_data_table(self, date):
        sql_create_table_day_data = ("CREATE TABLE IF NOT EXISTS day" + date +
                                     "(id integer PRIMARY KEY, nazwa TEXT, "
                                     "data INTEGER, otwarcie REAL, max REAL, "
                                     "min REAL, tko REAL, wolumen INTEGER);")
        self.query(sql_create_table_day_data)

    def get_company_all_data(self, company):
        self.query("SELECT * FROM tasks WHERE priority=?", (priority,))

    def __del__(self):
        self._db_connection.close()


def automatic_update():
    # pobierz najnowsze dane z bossa
    link = "https://info.bossa.pl/pub/ciagle/mstock/sesjacgl/sesjacgl.prn"
    f = urlopen(link)
    stock_data = f.read().decode("utf-8")
    date = stock_data.split('\r\n')[0].split(',')[1]
    print(f"BOS SA dane z {date}")

    db = MySqliteDb()
    if not db.table_in_db(f'day{date}'):
        print(f'Uaktualniam baze o dane z dnia: {date}!!!')
        db.create_day_data_table(date)
        current_data = [(x.split(',')) for x in stock_data.split('\r\n')]
        for row in current_data:
            if len(row) == 7:
                db.query(
                    f'''INSERT INTO day{date} (nazwa, data, otwarcie, max, min,
                        tko, wolumen) VALUES (?,?,?,?,?,?,?)''', row)
        db._db_connection.commit()
    else:
        print(f'Baza zawiera najnowsze dane z dnia: {date}')
    return db


def data_prn_file():
    folder_path = str(Path().absolute()) + '\\DB\\'
    files = []
    for r, d, f in os.walk(folder_path):
        for file in f:
            if '.prn' in file:
                files.append(os.path.join(r, file))
    return files


# glowna petla
database = automatic_update()
while True:
    choice = input(
        '================\n' + '1 obecna sciezka\n2 plot[test]\n3 dane z pliku\n0 wyjscie\n' +
        '================\n')

    if choice == '1':
        print('Sciezka: ' + str(Path().absolute()))
    if choice == '2':
        plt.plot([1, 2, 3, 4])
        plt.ylabel('some numbers')
        plt.show()
    if choice == '3':
        data_files = data_prn_file()
        print(data_files)
        file_choice = input(f'Wybierz nr pliku [0-{len(data_files) - 1}]: ')
        if int(file_choice) > len(data_files) - 1 or int(file_choice) < 0:
            print('Zly numer pliku')
            continue
        with open(data_files[int(file_choice)]) as f:
            data = f.read().split('\n')
            date = data[0].split(',')[1]
            print(f'{date}')
            if not database.table_in_db(f'day{date}'):
                print(f'Tworze tabele day{date}')
                database.create_day_data_table(date)
                for row in [x.split(',') for x in data]:
                    if len(row) == 7:
                        database.query(
                            f'''INSERT INTO day{date} (nazwa, data, otwarcie,
                            max, min, tko, wolumen) VALUES (?,?,?,?,?,?,?)''',
                            row)
                database._db_connection.commit()
            else:
                print(f'Baza zawiera dane z dnia: {date}')

    if choice == '0':
        break
