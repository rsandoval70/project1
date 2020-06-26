import os
import requests
import json

from flask import Flask, session, request, render_template, jsonify
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

#setup Api Goodreads

keyg = "34Flgj12URyZDMqbCp4bQ"

@app.route("/")
def index():
    if 'notes' not in session:
        session['notes'] = []
    note="1,"
    session['notes'].append(note)
    return render_template("index.html")

@app.route("/validate", methods=["POST"])
def validate():
    """Validate Login"""

    # Get form information.
    username = request.form.get("login")
    upassword = request.form.get("upassword")

    # Make sure user exists.
    user = db.execute("SELECT pwd, id FROM users WHERE username = :username", {"username": username}).fetchone()
    if user is None:
        return render_template("error.html", message="User doesn´t exist")
    if user.pwd == upassword:
        session['mySession'] = [user.id,username]
        return render_template("search.html")
    return  render_template("error.html", message="Password is incorrect")


@app.route("/books", methods=["POST"])
def books():
    """List Books"""
    #if session.get("myS") is None:
    #    return render_template("error.html", message="No hay session" )
    # Get form information.
    criteria = request.form.get("criteria")
    try:
        searchcriteria = int(request.form.get("searchcriteria"))
    except ValueError:
        return render_template("error.html", message="search type invalid")

    if searchcriteria == 1:
        books = db.execute("SELECT * FROM Books Where isbn like :criteria",{"criteria":'%' + criteria + '%'}).fetchall()
    elif searchcriteria == 2:
           books = db.execute("SELECT * FROM Books Where title like :criteria",{"criteria":'%' + criteria + '%'}).fetchall()
    elif searchcriteria == 3:
           books = db.execute("SELECT * FROM Books Where author like :criteria",{"criteria":'%' + criteria + '%'}).fetchall()
    return render_template("bookreview.html", books=books)


@app.route("/review", methods=["POST"])
def review():
    """check Review"""

    try:
        bookId = int(request.form.get("bookId"))
    except ValueError:
        return render_template("error.html", message="Book ID invalid")

    book = db.execute("SELECT * FROM books Where id = :criteria",{"criteria":bookId}).fetchone()
    if book is None:
        return render_template("error.html", message="No such Book.")


    reviews = db.execute("Select * FROM reviews where id_Book = :criteria",{"criteria":bookId}).fetchall()


    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": keyg, "isbns": book.isbn})


    # Use the json module to load CKAN's response into a dictionary.
    response_dict = json.loads(res.text)
    dataGodr = response_dict['books'][0]


    return render_template("submitreview.html", book=book,reviews=reviews, res=dataGodr)


@app.route("/submit", methods=["POST"])
def submit():
    """check Review"""
  # Get form information.
    try:
        book_id = int(request.form.get("id_book"))
    except ValueError:
        return render_template("error.html", message="Book ID invalid")

    try:
        user_id = int(request.form.get("id_user"))
    except ValueError:
        return render_template("error.html", message="User ID invalid")


    review = request.form.get("comment")
    try:
        rate = int(request.form.get("rating"))
    except ValueError:
        return render_template("error.html", message="User ID invalid")

# Make sure book exists.
    if db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).rowcount == 0:
        return render_template("error.html", message="No such Book with that id.")
    if db.execute("SELECT * FROM reviews WHERE id_user = :idu and id_book = :idb", {"idu": user_id,"idb": book_id},).rowcount == 0:
        db.execute("INSERT INTO reviews (id_user, id_book, review ,rate) VALUES (:user_id, :book_id , :review, :rate)",
                {"user_id": user_id, "book_id": book_id, "review": review, "rate": rate})
        db.commit()
        return render_template("success.html")
    else:
        return render_template("error.html", message="There are one review for this user")


@app.route("/api/books/<book_isbn>")
def book_api(book_isbn):
    """check Review"""
    if book_isbn == "":
        return jsonify({"error": "Invalid Book_id"}), 422
    book = db.execute("SELECT * FROM books Where isbn = :isbn",{"isbn":book_isbn}).fetchone()
    if book is None:
        return jsonify({"error": "Book does not exist in  this database"}), 422
    reviews = db.execute("select books.title, books.author, books.year, books.isbn, count(*) as review_count , avg(Rate) as average_score from books LEFT JOIN reviews ON books.id = reviews.id_book where  books.isbn = :isbn Group by books.id",{"isbn":book_isbn}).fetchall()
    return jsonify({
    "tittle": reviews[0].title,
    "author": reviews[0].author,
    "year": reviews[0].year,
    "isbn": reviews[0].isbn,
    "review_count": reviews[0].review_count,
    "average_score": "{:.2f}".format(reviews[0].average_score)
    })
