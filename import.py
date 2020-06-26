import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader =  csv.reader(f)
    cont = 1
    for  isbn, title, author, year in reader:
     if cont > 1:
        db.execute("INSERT INTO books(isbn, title, author, year) values (:isbn, :title, :author, :year)",
        {"isbn": isbn, "title": title,"author": author, "year": year})
        print(f"Added Book with Isbn: {isbn}, title: {title}, author: {author}, year: {year}")
     cont += 1
    db.commit()

if __name__  == "__main__"    :
    main()
