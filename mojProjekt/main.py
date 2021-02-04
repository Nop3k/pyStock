import os
from urllib.request import urlopen
from difflib import get_close_matches

import matplotlib.pyplot as plt
import pandas as pd
import pymongo
import datetime

# nagłówki tabeli
keys = ['nazwa', 'data', 'otwarcie', 'max', 'min', 'tko', 'wolumen']
# formatowanie liczb wyświetlanych przez pandas
pd.set_option("display.float_format", '{:,.2f}'.format)


# funkcja pobiera najnowsze dane z bossa
def automatic_update():
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

        # przetwórz dane z bossa - utwórz listę i rzutuj zmienne
        stock_data_listed = [x.split(',') for x in stock_data.split('\r\n')]
        stock_data_listed.pop()
        for stock in stock_data_listed:
            stock[1] = int(stock[1])
            stock[2] = float(stock[2])
            stock[3] = float(stock[3])
            stock[4] = float(stock[4])
            stock[5] = float(stock[5])
            stock[6] = float(stock[6])

        # dzień z którego pobrało dane
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

    # pokaż menu
    while True:
        menu = input(
            '================\n1 update z .prn\n2 update z neta\n3 plot\n' +
            '0 wyjscie\n================\n')
        # menu = "3"
        if menu == '1':

            # Lista plikow .prn
            data_path = os.path.join(os.getcwd(), 'notowania')
            print('Sciezka dla plików: ' + data_path)
            file_list = [file for file in
                         os.listdir(data_path) if
                         file.endswith('.prn')]
            for idx in range(len(file_list)):
                # utwórz ścieżkę do kolejnych plików prn w folderze
                file_path = f'{data_path}\\{file_list[idx]}'

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
                        f" z dnia {date}")

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
            # company = input('Wybierz spółkę do wyświetlenia\n').upper()
            company = "CDPROJEKT"
            # pomóż wybrać spółkę po nazwie - wyszukiwarka
            query = {}
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

            # wybierz zakres danych do pokazania
            today = datetime.date.today()
            choice = input('Wybierz okres:\n1 ostatnie 7 dni\n' +
                           '2 ostatnie 30 dni\n3 ostatnie 90 dni' +
                           '\n4 wlasny\n0 wszystko\n')
            if choice == '1':
                week_ago = (today - datetime.timedelta(days=8)).strftime(
                    '%Y%m%d')
                query['data'] = {'$gte': int(week_ago)}
            if choice == '2':
                month_ago = (today - datetime.timedelta(days=31)).strftime(
                    '%Y%m%d')
                query['data'] = {'$gte': int(month_ago)}
            if choice == '3':
                three_month_ago = (
                        today - datetime.timedelta(days=91)).strftime(
                    '%Y%m%d')
                query['data'] = {'$gte': int(three_month_ago)}
            if choice == '4':
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

                # TODO: funkcja rysująca wykresy
                # przygotuj okno z wykresami
                fig, ax1 = plt.subplots()
                plt.xticks(rotation=45)
                plt.autoscale()
                plt.title(query['nazwa'])

                # przygotuj wykres data/wolumen
                ax1.bar(result_data_frame['data'],
                        result_data_frame['wolumen'],
                        color='b')
                ax1.set_ylabel('Il. transakcji', fontsize=10)
                ax1.set_xlabel('Data', fontsize=10)
                ax1.tick_params(axis='x', labelsize=8)
                ax1.legend(loc="upper left", labels=['wolumen'],
                           fontsize=6)

                # skopiuj dane z wykresu 1 i przygotuj wykres data/otwarcie
                ax2 = ax1.twinx()
                ax2.plot(result_data_frame['data'],
                         result_data_frame['otwarcie'], '-oc',
                         result_data_frame['data'],
                         result_data_frame['max'], '^g',
                         result_data_frame['data'],
                         result_data_frame['min'], 'vr')
                ax2.set_ylabel('PLN', fontsize=10)
                ax2.legend(loc="upper right", labels=['otwarcie'],
                           fontsize=6)
                # statystyka
                df = result_data_frame[
                    ['data', 'otwarcie', 'max', 'min', 'tko', 'wolumen']]
                # zachowaj najnowsze notowanie
                newest = df[df['data'] == df['data'].max()].set_index('data')
                # pomiń najnowsze notowanie
                df = df[df['data'] != df['data'].max()].set_index('data')
                # pokaż statystyki
                statistics = df.agg(['mean', 'median', 'mad', 'min', 'max'])
                # porównaj najnowsze dane
                comparison = newest.append(
                    newest.div(
                        statistics[statistics.index == "mean"].values) * 100)
                print(statistics)
                print(
                    "\nPierwszy wiersz:ostatni kurs\n" +
                    "Drugi wiersz:jaki % średnich wartości danego okresu" +
                    " stanowi nowy kurs")
                print(comparison)

                # wyświetl wykres
                plt.show()

        if menu == '4':
            # TODO: funkcja scrapująca dane 'realtime' i rysująca
            pass

        if menu == '5':
            # TODO: funkcja porówniania dwóch spółek?
            pass

        if menu == '0':
            break
        break
