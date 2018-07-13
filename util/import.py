import os

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import scoped_session, sessionmaker

import csv

def main():
    # Check for environment variable
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is not set")

    # Set up database
    engine = create_engine(os.getenv("DATABASE_URL"))
    db = scoped_session(sessionmaker(bind=engine))

    # Read in csv
    f = open("books.csv")
    reader = csv.reader(f)

	# Skip schema line
    next(reader)

    for isbn, title, author, year in reader:
	    db.execute("""
		INSERT INTO books (isbn, title, author, year)
		VALUES (:isbn, :title, :author, :year)
		""", {"isbn": isbn, "title": title, "author": author, "year": year})

    db.commit()

if __name__ == "__main__":
	main()
