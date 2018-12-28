import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn,title,author,year in reader:
        try:
           ISBN = str(isbn)
           TITLE = str(title)
           AUTHOR = str(author)
           YEAR = int(year)
           db.execute("INSERT INTO book(isbn,title,author,year) VALUES(:isbn, :title, :author, :year)",{"isbn":ISBN, "title":TITLE, "author":AUTHOR, "year":YEAR})
           print(f"Added BOOK OF {ISBN} AND {TITLE} AUTHOR {AUTHOR}  WRONG {YEAR}.")
        except ValueError:
           print("wrong")

    db.commit()


if __name__ == "__main__":
    main()