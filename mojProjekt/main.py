import os
from pathlib import Path
from urllib.request import urlopen
from difflib import get_close_matches

import matplotlib.pyplot as plt
import pandas as pd
import pymongo
import pprint
import datetime

keys = ['nazwa', 'data', 'otwarcie', 'max', 'min', 'tko', 'wolumen']


def automatic_update():
    # pobierz najnowsze dane z bossa
    link = "https://info.bossa.pl/pub/ciagle/mstock/sesjacgl/sesjacgl.prn"
    try:
        response = urlopen(link)
    except URLError as e:
        if hasattr(e, 'reason'):
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
        elif hasattr(e, 'code'):
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
    else:
        stock_data = response.read().decode("utf-8")

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
        stock_data_documented = [{key: value for key, value in zip(keys, row)}
                                 for
                                 row
                                 in stock_data_listed]
        return int(date), stock_data_documented


# glowna petla
if __name__ == '__main__':
    # połącz z bazą danych i otwórz kolekcję
    my_client = pymongo.MongoClient("mongodb://localhost:27017/")
    my_db = my_client["myDatabase"]
    collection = my_db["notowania"]
    while True:
        menu = input(
            '================\n1 update z .prn\n2 update z neta\n3 plot\n' +
            '0 wyjscie\n================\n')

        if menu == '1':
            # Pokaz gdzie jestem
            print('Sciezka: ' + str(Path().absolute()))

            # Lista plikow .prn
            file_list = [file for file in
                         os.listdir(Path().absolute()) if
                         file.endswith('.prn')]
            for idx in range(len(file_list)):
                # utwórz ścieżkę do kolejnych plików prn w folderze
                file_path = f'{Path().absolute()}\\{file_list[idx]}'

                # Przetworz plik .prn odpowiednie stringi do intów/floatów
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

                # przygotuj dokumenty
                file_data_documented = [
                    {key: value for key, value in zip(keys, row)} for row
                    in file_data_listed]

                # upewnij się, że dane są nowe
                if collection.find_one({"data": date}):
                    print(f"Baza zawiera dane z dnia {date}.")
                else:
                    result = collection.insert_many(file_data_documented)
                    print(
                        f"Dodano {len(result.inserted_ids)} notowan"
                        f"z dnia {date}")

        if menu == '2':
            # pobierz dane ze strony WWW
            date, data = automatic_update()

            # TODO: funkcja sprawdzająca bazę na obecność danych
            # sprawdź, czy baza posiada "nowe" dane
            if collection.find_one({"data": date}):
                print(f"Baza zawiera dane z dnia {date}.")
            else:
                result = collection.insert_many(data)
                print(
                    f"Dodano {len(result.inserted_ids)} notowan z dnia {date}")

        if menu == '3':
            # TODO: funkcja pobierająca dane z bazy
            # wybierz spółkę
            company = input('Wybierz spółkę do wyświetlenia\n').upper()
            query = {}

            # pomóż wybrać spółkę po nazwie
            unique_companies = collection.distinct('nazwa')
            inquiry = get_close_matches(company, unique_companies)
            if not inquiry:
                print(f'Nie znaleziono spółki {company}.')
            elif company not in unique_companies:
                print(f"Czy chodziło o:")
                print({key: value for key, value in enumerate(inquiry)})
                query['nazwa'] = inquiry[int(input())]
            else:
                query['nazwa'] = company

            today = datetime.date.today()
            choice = input(
                'Wybierz okres:\n1 ostatnie 7 dni\n2 ostatnie 30 dni\n3 wlasny\n0 wszystko\n')
            if choice == '1':
                week_ago = (today - datetime.timedelta(days=8)).strftime(
                    '%Y%m%d')
                query['data'] = {'$gte': int(week_ago)}
            if choice == '2':
                month_ago = (today - datetime.timedelta(days=31)).strftime(
                    '%Y%m%d')
                query['data'] = {'$gte': int(month_ago)}
            if choice == '3':
                # TODO: własny okres notowań
                continue
            print(query)

            # pobierz z bazy dane i utwórz dataframe
            result_data_frame = pd.DataFrame(
                collection.find(query))

            # sprawdź, czy poprawnie wyszukano
            if result_data_frame.empty:
                print(f'Puste dane dla {company}.')
            else:
                # konwertuj datę z int do datetime
                result_data_frame['data'] = pd.to_datetime(
                    result_data_frame['data'].astype(int), format='%Y%m%d')

                # uporządkuj wyniki zgodnie z datą
                result_data_frame.sort_values(by=['data'], inplace=True)
                print(result_data_frame)

                # TODO: funkcja rysująca wykresy
                # przygotuj okno z wykresami
                fig, ax1 = plt.subplots()
                plt.xticks(rotation=45)
                plt.autoscale()
                plt.tight_layout(4)
                plt.title(query['nazwa'])

                # przygotuj wykres data/wolumen
                ax1.bar(result_data_frame['data'],
                        result_data_frame['wolumen'],
                        color='c')
                ax1.set_ylabel('Il. transakcji', fontsize=10)
                ax1.set_xlabel('Data', fontsize=10)
                ax1.tick_params(axis='x', labelsize=8)
                ax1.legend(loc="upper left", labels=['wolumen'],
                           fontsize=6)

                # skopiuj dane z wykresu 1 i przygotuj wykres data/otwarcie
                ax2 = ax1.twinx()
                ax2.plot(result_data_frame['data'],
                         result_data_frame['otwarcie'],
                         '-o')
                ax2.set_ylabel('PLN', fontsize=10)
                ax2.legend(loc="upper right", labels=['otwarcie'],
                           fontsize=6)

                # wyświetl wykres
                plt.show()

        if menu == '4':
            # TODO: funkcja scrapująca dane 'realtime' i rysująca
            pass

        # TODO: funkcja porówniania dwóch spółek?
        if menu == '0':
            break
