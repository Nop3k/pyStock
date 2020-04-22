import sqlite3
from urllib.request import urlopen
from pathlib import Path
from sqlite3 import Error


# funkcja utworz plik DB (jesli nie ma) lub polaczenie (jesli jest plik)
def polacz_bd(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print('Wersja utworzonej bazy SQLite3: ' + sqlite3.version)
        return conn
    except Error as e:
        print(e)
        return conn


# funkcja stworz tabele
def stworz_tabele(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def dodaj_dane_bd(conn,dane):
    """
    Create a new project into the projects table
    :param conn:
    :param project:
    :return: project id
    """
    sql = f'''INSERT INTO dane{data}(nazwa, data, otwarcie, max, min, tko, wolumen)
            VALUES (?,?,?,?,?,?,?)'''
    c = conn.cursor()
    c.execute(sql, dane)
    return c.lastrowid

def sprawdz_czy_pusta_tabela(conn):
    sql = f'''SELECT count(*) FROM (SELECT 0 FROM dane{data});'''
    c = conn.cursor()
    c.execute(sql)
    return True if c.fetchone()[0] == 0 else False


# pobierz najnowsze dane z bossa
link = "https://info.bossa.pl/pub/ciagle/mstock/sesjacgl/sesjacgl.prn"
f = urlopen(link)
daneGielda = f.read().decode("utf-8")

# utworz plik DB (jesli nie ma) lub polaczenie (jesli jest plik)
baza = polacz_bd(str(Path().absolute()) + r"\DB\pyGieldaDB.db")

# glowna petla
while True:
    data = str(daneGielda.split('\r\n')[0].split(',')[1])
    wybor = input(
        '================\n' + '1 zarzadzaj BD\n2 obecna sciezka\n3 daneGielda\n0 wyjscie\n' + '================\n')
    if wybor == '1':
        wybor2 = input(f'1 stworz tabele DB\n2 Zapisz dane z {data}\n0 powrot\n')

        if wybor2 == '1':
            sql_stworz_tabele_dzien = ("CREATE TABLE IF NOT EXISTS dane" + data + \
                                       "(id integer PRIMARY KEY, nazwa TEXT, "
                                       "data INTEGER, otwarcie REAL, max REAL, "
                                       "min REAL, tko REAL, wolumen INTEGER);")
            print(sql_stworz_tabele_dzien)
            if baza is not None:
                stworz_tabele(baza, sql_stworz_tabele_dzien)
            else:
                print("Error! cannot create the database connection.")

        if wybor2 == '2':
            with baza:
                if sprawdz_czy_pusta_tabela(baza):
                    for notowanie in  daneGielda.split('\r\n'):
                        if len(notowanie) > 0:
                            dodaj_dane_bd(baza,notowanie.split(','))

        if wybor2 == '0':
            continue

    if wybor == '2':
        print('Sciezka: ' + str(Path().absolute()))

    if wybor == '3':
        print(daneGielda)

    if wybor == '0':
        break

if baza:
    baza.close()
