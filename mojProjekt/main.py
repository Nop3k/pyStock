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

    # przetworz dane z bossa
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

            # Przetworz wybrany plik .prn
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

            if collection.find_one({"data": date}):
                print(f"Baza zawiera dane z dnia {date}.")
            else:
                result = collection.insert_many(file_data_documented)
                print(
                    f"Dodano {len(result.inserted_ids)} notowan z dnia {date}")

        if choice == '2':
            result_data_frame = pd.DataFrame(
                collection.find({'nazwa': 'CDPROJEKT'}))
            result_data_frame['data'] = pd.to_datetime(
                result_data_frame['data'].astype(int), format='%Y%m%d')
            result_data_frame.sort_values(by=['data'], inplace=True)
            print(result_data_frame)

            fig, ax1 = plt.subplots()
            ax1.plot(result_data_frame['data'], result_data_frame['otwarcie'])
            ax1.set_xlabel('Data')
            ax1.set_ylabel('PLN')
            ax1.autoscale()

            ax2 = ax1.twinx()
            result_data_frame.plot(kind='bar', x='data', y='wolumen', ax=ax2)
            ax2.set_ylabel('Il. transakcji')
            ax2.autoscale()

            plt.show()

        if choice == '3':
            date, data = automatic_update()
            if collection.find_one({"data": date}):
                print(f"Baza zawiera dane z dnia {date}.")
            else:
                result = collection.insert_many(data)
                print(
                    f"Dodano {len(result.inserted_ids)} notowan z dnia {date}")
        if choice == '0':
            break
