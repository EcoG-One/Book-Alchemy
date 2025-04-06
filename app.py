import os
from datetime import datetime
from data_models import Author, Book, db
from flask import Flask, render_template, request
# import requests (in case we
#     prefer to build and use a local book cover storage.)

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = "./data"
DB_NAME = "library.sqlite"
FULL_DB_PATH = os.path.join(ROOT_PATH, DB_FOLDER, DB_NAME)

app = Flask(__name__)
app.config.from_mapping(
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{FULL_DB_PATH}"
)

db.init_app(app)

# create db tables based on data_models ,
# called only once for table creation or database got cancelled
if not os.path.exists(FULL_DB_PATH):
    with app.app_context():
        db.create_all()


@app.route("/")
def index():
    """
    Home page route.
    It handles sorting and searching books in the library.
    Displays the list of books along with the total count of books.
    :return: Rendered HTML template for the home page.
    """
    sort = Book.title  # default sorting
    book_count = Book.count_books(db.session)
    if "sort" in request.args:
        sort: str = request.args["sort"]
    books = db_get_books(sort)

    if "search" in request.args:
        search = request.args["search"]
        search_results = db_search_books(search)
        print(search_results)
        if search_results:
            books = search_results
        else:
            books = []

    return render_template("home.html", books=books, book_count=book_count)


@app.route("/add_author", methods=["GET", "POST"])
def add_author():
    """
    Route to the add a new author page.
    Handles both GET and POST requests. For GET, it renders the author
    addition form. For POST, it adds a new author to the database.
    :return: Rendered HTML template for adding an author
     and confirmation message.
    """
    if request.method == "POST":
        name = request.form["name"]
        birthdate = request.form["birthdate"]
        existing_author = Author.query.filter_by(name=name,
                                                 birth_date=birthdate).first()
        if existing_author:
            return render_template(
    "add_author.html", message="Author already exists!"), 404
        new_author = db_add_author(request.form)
        return render_template("add_author.html", item=new_author)

    return render_template("add_author.html")


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    """
    Route to add a new book page.
    Handles both GET and POST requests. For GET, it renders the book
    addition form. For POST, it adds a new book to the database.
    :return: Rendered HTML template for adding a book
    or a confirmation message.
    """
    current_year = datetime.now().year
    if request.method == "POST":
        isbn = request.form["isbn"]
        existing_isbn = Book.query.filter_by(isbn=isbn).first()
        if existing_isbn:
            authors = db_get_authors()
            return render_template("add_book.html", authors=authors,
                current_year=current_year, message="Book already exists!"), 404
        new_book = db_add_book(request.form)
        authors = db_get_authors()
        return render_template("add_book.html", item=new_book, authors=authors,
                current_year=current_year)
    authors = db_get_authors()
    return render_template(
"add_book.html", authors=authors, current_year=current_year
    )


@app.route("/book/<int:book_id>/delete", methods=["GET"])
def delete_book(book_id: int):
    """
    Route to delete a book by its ID.
    Deletes a book from the database by its ID if found,
    and renders home page template with a confirmation message.
    :param book_id: The ID of the book to delete.
    :return: Rendered HTML home page template.
    """
    book = db.session.execute(
        db.select(Book).where(Book.book_id == book_id)
    ).scalar_one_or_none()
    books = Book.query.all()
    book_count = Book.count_books(db.session)
    if not book:
        return render_template(
            "home.html", books=books, book_count=book_count,
            message="Book not found"), 404
    author_id = book.author_id
    db.session.delete(book)
    message = "Book deleted."
    existing_author = Book.query.filter_by(author_id=author_id).first()
    if not existing_author:
        author = Author.query.get_or_404(author_id)
        db.session.delete(author)
        message = "Book deleted. Also book's author deleted."
    db.session.commit()
    books = Book.query.all()
    book_count = Book.count_books(db.session)
    return render_template(
        "home.html", books=books, book_count=book_count, message=message)


def db_get_books(sort: str):
    """
    Sorts books from the database based on the given sort parameter.
    :param sort: Column to sort by.
    :return: A list of books sorted by the specified field.
    """
    sort_options = {
        "title": Book.title,
        "author": Author.name,
        "publication_year": Book.publication_year,
        "rating": Book.rating,
    }

    sort_by = sort_options.get(sort, Book.title)
    if sort == "rating":
        result = (
            (
                db.session.execute(
                    db.select(Book).join(Book.author).order_by(sort_by.desc())
                )
            )
            .scalars()
            .all()
        )
    else:
        result = (
            (
                db.session.execute(
                    db.select(Book).join(Book.author).order_by(sort_by)
                )
            )
            .scalars()
            .all()
        )
    return result


def db_search_books(search: str):
    """
    Searches for books by title using a case-insensitive substring match.
    :param search: The search term to look for in book titles.
    :return: A list of books matching the search term.
    """
    search = f"%{search.lower()}%"
    result = (
        (db.session.execute(db.select(Book).where(Book.title.like(search))))
        .scalars()
        .all()
    )
    return result


def db_get_authors():
    """
    Fetches all authors from the database, sorted alphabetically by name.
    :return: A list of all authors.
    """
    result = (
        db.session.execute(db.select(Author).order_by(Author.name))
        .scalars()
        .all()
    )
    return result


def db_add_author(request: dict):
    """
    Adds a new author to the database.
    :param request: A dictionary containing author data.
    :return: The new Author object.
    """
    name: str = request.get("name", None)
    birth_date: str = request.get("birthdate", None)
    death_date: str = request.get("date_of_death", None)
    new_author = Author(
        name=name,  # type: ignore
        birth_date=birth_date,  # type: ignore
        date_of_death=death_date,  # type: ignore
    )
    db.session.add(new_author)
    db.session.commit()
    return new_author


'''def get_book_cover(isbn):
    Retrieves book covers from API and saves them locally, in case we
    prefer to build and use a local book cover storage.

    url = 
    f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"
    response = requests.get(url)

    if response.status_code == 200:
        with open(f"static/images/{isbn}.jpg", "wb") as file:
            file.write(response.content)
        print(f"Book cover for ISBN {isbn} saved as {isbn}.jpg")
        return f"static/images/{isbn}.jpg"
    else:
        print(f"Failed to retrieve book cover for ISBN {isbn}")
        return "static/images/book.jpg" 
    '''


def db_add_book(request):
    """
    Adds a new book to the database.
    :param request: A dictionary containing book data.
    :return: The new Book object.
    :raises ValueError: If the specified author
            does not exist in the database.
    """
    title: str = request.get("title")
    isbn: str = request.get("isbn")
    author_id: str = request.get("author")
    pub_year: str = request.get("publication_year")
    summary: str = request.get("summary")
    img_url = \
            f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
    # img_url = get_book_cover(new_book.isbn)
    #    (in case we prefer to build local book cover storage)
    rating: str = request.get("rating")

    # get author from author_name for author.id in book
    author = db.session.execute(
        db.select(Author).where(Author.id == int(author_id))
    ).scalar_one_or_none()

    if not author:
        raise ValueError("Author not found in database.")

    new_book = Book(
        title=title,
        isbn=isbn,
        publication_year=pub_year,
        author_id=author.id,
        summary=summary,
        img_url=img_url,
        rating=rating,
    )
    db.session.add(new_book)
    db.session.commit()
    return new_book


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
