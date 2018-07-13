import os

from flask import Flask, session
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
    username = session.get("user_id") ? db.execute("SELECT username FROM users WHERE id = :id", {"id": session["user_id"]}).first().username : None

    books = []
    if request.method == "POST":
        query = request.form.get("query")
        books = db.execute("""
        SELECT title, author
        FROM books
        WHERE isbn LIKE :query OR title LIKE :query OR author LIKE :query
        """, {"query": '%' + query + '%'}).fetchall()

    return render_template("index.html", books=books, username=username)

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

def location_data(zipcode):
    locations_row = db.execute("SELECT * FROM locations WHERE zip = :zipcode", {"zipcode": zipcode}).first()

    if not locations_row:
        return abort(404, f'Your zipcode [{zipcode}] is not valid or does not exist. We only support United States zipcodes currently.')

    checkins_row = db.execute("SELECT COUNT(*) FROM checkins WHERE zip = :zipcode", {"zipcode": zipcode}).first()

    return {
        "place_name": locations_row.city.capitalize(),
        "state": locations_row.state,
        "latitude": float(locations_row.lat),
        "longitude": float(locations_row.lon),
        "zip": locations_row.zip,
        "population": locations_row.population,
        "check_ins": checkins_row.count
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

@app.route("/api/<string:zipcode>")
def api(zipcode):
    return jsonify(location_data(zipcode))
