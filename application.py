import os

from flask import Flask, session, request, render_template, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/", methods=["GET", "POST"])
def index():
    username = db.execute("SELECT username FROM users WHERE id = :id", {"id": session["user_id"]}).first().username \
    if session.get("user_id") else None

    searched = False
    books = []
    if request.method == "POST":
        searched = True
        query = request.form.get("query")
        books = db.execute("""
        SELECT isbn, title, author FROM books
        WHERE isbn LIKE :query OR title LIKE :query OR author LIKE :query
        """, {"query": '%' + query + '%'}).fetchall()
        if not books:
            flash('Your query returned no matches.')

    return render_template("index.html", searched=searched, books=books, username=username)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        error = None

        if not username:
            error = 'Username is required'
        elif not password:
            error = 'Password is required'
        elif db.execute("SELECT id FROM users WHERE username=:username", {"username": username}).first():
            error = f'User with username [{username}] already exists'

        if error is None:
            db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
            {"username": username, "password": password})
            db.commit()
            flash("Success!")
            return redirect(url_for('index'))

        flash(error)

    return render_template('register.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        error = None

        if not username:
            error = 'Username is required'
        elif not password:
            error = 'Password is required'

        user = db.execute("SELECT * FROM users WHERE username=:username", {"username": username}).first()
        if not user:
            error = 'Username incorrect'
        elif password != user.password:
            error = 'Password incorrect'

        if error is None:
            session["user_id"] = user.id
            return redirect(url_for('index'))

        flash(error)

    return render_template('login.html')

@app.route("/logout")
def logout():
    session.pop("user_id")
    return redirect(url_for('index'))

@app.route("/books/<string:isbn>", methods=["GET", "POST"])
def books(isbn):
    allow_review = True
    data = book_data(isbn)

    if request.method == "GET":

    else:
        comment = request.form.get('comment')
        rating = request.form.get('rating')
        db.execute("""
        INSERT INTO reviews (comment, rating, created_at, user_id, book_isbn)
        VALUES (:comment, :user_id, :zipcode)
        """, {"comment": comment, "rating": rating})
        db.commit()


    return render_template('book.html')

@app.route("/api/<string:isbn>")
def api(isbn):
    return jsonify(book_data(isbn))

def book_data(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).first()

    if not book:
        return abort(404, f'No book exists with isbn [{isbn}].')

    review_count = db.execute("SELECT COUNT(*) FROM reviews WHERE book_isbn = :isbn", {"isbn": isbn}).first().count
    average_score = db.execute("SELECT AVG(rating::DECIMAL) FROM reviews WHERE book_isbn = :isbn", {"isbn": isbn}).first().avg

    return {
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": review_count,
        "average_score": average_score
    }

@app.route("/locations/<string:zipcode>", methods=["GET", "POST"])
def locations(zipcode):
    allow_checkin = False
    data = location_data(zipcode)
    checkins = db.execute("SELECT username, time, comment FROM users, checkins WHERE checkins.zip = :zipcode",
        {"zipcode": zipcode}).fetchall()

    if request.method == "GET":
        if 'user_id' in session:
            cur_user_checkin = db.execute("""
            SELECT username, time, comment FROM users, checkins WHERE checkins.zip = :zipcode AND users.id = :id
            """, {"zipcode": zipcode, "id": session['user_id']}).first()
            if not cur_user_checkin:
                allow_checkin = True
    else:
        comment = request.form.get('comment')
        db.execute('INSERT INTO checkins (comment, user_id, zip) VALUES (:comment, :user_id, :zipcode)',
            {"comment": comment, "user_id": session['user_id'], "zipcode": zipcode})
        db.commit()

    return render_template('location.html', data=data, checkins=checkins, allow_checkin=allow_checkin)
