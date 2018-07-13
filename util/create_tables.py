import os

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import scoped_session, sessionmaker

def main():
    # Check for environment variable
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is not set")

    # Set up database
    engine = create_engine(os.getenv("DATABASE_URL"))
    db = scoped_session(sessionmaker(bind=engine))

    db.execute("""
    CREATE TABLE books (
	    isbn VARCHAR PRIMARY KEY,
	    title VARCHAR NOT NULL,
	    author VARCHAR NOT NULL,
	    year INTEGER NOT NULL
	)
	""")

    db.execute("""
	CREATE TABLE users (
	    id SERIAL PRIMARY KEY,
	    username VARCHAR NOT NULL,
	    password VARCHAR NOT NULL
	)
	""")

    db.execute("""
	CREATE TABLE reviews (
	    id SERIAL PRIMARY KEY,
	    comment TEXT NOT NULL,
	    rating INTEGER NOT NULL CHECK(rating > 0 AND rating < 6),
	    created_at TIMESTAMP DEFAULT NOW(),
	    user_id INTEGER REFERENCES users NOT NULL UNIQUE,
	    book_isbn VARCHAR REFERENCES books NOT NULL
	)
	""")

    db.commit()

if __name__ == "__main__":
    main()
