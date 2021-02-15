# pyStock
>Private project to learn python, mongoDB, pandas to operate on stock exchange.
# Requirements
* python3
* Local MongoDB database "myDatabase" with collection "stock data"
# How to use
4 Options in menu
Choose by typing 1 2 3 or 0 and pressing enter

1 - In the folder "stock data" are stored some files with .prn extension in a specific format (same as BOSSA.pl end of day stock data). You can put more files there.
This option will add all the new data included in all the files from the folder to the database collection.

2 - Connects automatically to BOSSA.pl and if online data is new adds to collection.

3 - Here you can show the gathered data. After selecting this option you have to choose the company or index to check - by typing it's name (e.g. WIG).
Don't worry it will help you choose the name if you didn't type it wrong - it will show the closest result. 
Just choose one from list (by typing 0 ... etc and enter again).

0 - Exits the loop and finishes the program.
