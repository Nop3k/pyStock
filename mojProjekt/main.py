from urllib.request import urlopen
from pathlib import Path
import matplotlib.pyplot as plt
import os
import pymongo
import pprint
import pandas as pd


def automatic_update():
    # pobierz najnowsze dane z bossa
    link = "https://info.bossa.pl/pub/ciagle/mstock/sesjacgl/sesjacgl.prn"
    f = urlopen(link)
    stock_data = f.read().decode("utf-8")

    # przetwórz dane z bossa
    stock_data_listed = [x.split(',') for x in stock_data.split('\r\n')]
    stock_data_listed.pop()
    for stock in stock_data_listed:
        stock[1] = int(stock[1])
        stock[2] = float(stock[2])
        stock[3] = float(stock[3])
        stock[4] = float(stock[4])
        stock[5] = float(stock[5])
        stock[6] = float(stock[6])
    date = stock_data_listed[0][1]
    print(f"BOS SA dane z {date}")

    # przygotuj dokumenty
    keys = ['nazwa', 'data', 'otwarcie', 'max', 'min', 'tko', 'wolumen']
    stock_data_documented = [{key: value for key, value in zip(keys, l)} for l
                             in stock_data_listed]
    return int(date), stock_data_documented


# glowna petla
if __name__ == '__main__':
    # połącz z bazą danych i otwórz kolekcję
    my_client = pymongo.MongoClient("mongodb://localhost:27017/")
    my_db = my_client["myDatabase"]
    collection = my_db["notowania"]
    while True:
        choice = input(
            '================\n' + '1 obecna sciezka\n2 plot[test]\n3 update\n0 wyjscie\n' +
            '================\n')

        if choice == '1':
            # Pokaz gdzie jestem
            print('Sciezka: ' + str(Path().absolute()))

            # Lista plikow .prn
            file_list = {idx: file for idx, file in
                         enumerate(os.listdir(Path().absolute())) if
                         file.endswith('.prn')}
            pprint.pprint(file_list)
            file_no = input('Wybierz plik do zaimportowania do bazy danych:\n')
            file_path = f'{Path().absolute()}\{file_list[int(file_no)]}'

            # Przetworz wybrany plik .prn stringi do intów/floatów
            # kolejno 0='nazwa', 1='data', 2='otwarcie', 3='max', 4='min',
            #         5='tko', 6='wolumen'
            with open(file_path, 'r') as file:
                file_data = file.read().split('\n')
            file_data.pop()
            file_data_listed = [x.split(',') for x in
                                file_data]
            for stock in file_data_listed:
                stock[1] = int(stock[1])
                stock[2] = float(stock[2])
                stock[3] = float(stock[3])
                stock[4] = float(stock[4])
                stock[5] = float(stock[5])
                stock[6] = float(stock[6])
            date = file_data_listed[0][1]
            print(f"Wybrano plik z danymi z dnia {date}")

            # przygotuj dokumenty
            keys = ['nazwa', 'data', 'otwarcie', 'max', 'min', 'tko',
                    'wolumen']
            file_data_documented = [
                {key: value for key, value in zip(keys, l)} for l
                in file_data_listed]

            # upewnij się, że dane są nowe
            if collection.find_one({"data": date}):
                print(f"Baza zawiera dane z dnia {date}.")
            else:
                result = collection.insert_many(file_data_documented)
                print(
                    f"Dodano {len(result.inserted_ids)} notowan z dnia {date}")

        if choice == '2':
            # pobierz z bazy dane i utwórz dataframe
            result_data_frame = pd.DataFrame(
                collection.find({'nazwa': 'CDPROJEKT'}))

            # konwertuj datę z int do datetime
            result_data_frame['data'] = pd.to_datetime(
                result_data_frame['data'].astype(int), format='%Y%m%d')

            # uporządkuj wyniki zgodnie z datą
            result_data_frame.sort_values(by=['data'], inplace=True)
            print(result_data_frame)

            # przygotuj okno z wykresami
            fig, ax1 = plt.subplots()
            plt.xticks(rotation=45)
            plt.autoscale()
            plt.tight_layout(4)
            plt.title('CDPROJEKT')

            # przygotuj wykres data/wolumen
            ax1.bar(result_data_frame['data'], result_data_frame['wolumen'],
                    color='c')
            ax1.set_ylabel('Il. transakcji', fontsize=10)
            ax1.set_xlabel('Data', fontsize=10)
            ax1.tick_params(axis='x', labelsize=8)
            ax1.legend(loc="upper left", labels=['wolumen'], fontsize=6)

            # skopiuj dane z wykresu 1 i przygotuj wykres data/otwarcie
            ax2 = ax1.twinx()
            ax2.plot(result_data_frame['data'], result_data_frame['otwarcie'],
                     '-o')
            ax2.set_ylabel('PLN', fontsize=10)
            ax2.legend(loc="upper right", labels=['otwarcie'], fontsize=6)

            # wyświetl wykres
            plt.show()

        if choice == '3':
            # pobierz dane ze strony WWW
            date, data = automatic_update()

            # sprawdź, czy baza posiada "nowe" dane
            if collection.find_one({"data": date}):
                print(f"Baza zawiera dane z dnia {date}.")
            else:
                result = collection.insert_many(data)
                print(
                    f"Dodano {len(result.inserted_ids)} notowan z dnia {date}")

        if choice == '0':
            break
