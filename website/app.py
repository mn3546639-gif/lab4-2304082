from flask import Flask, render_template, request, redirect, session
import os
from decimal import Decimal, InvalidOperation
import pymysql
import bcrypt
from dotenv import load_dotenv
from flask_session import Session
from cachelib.file import FileSystemCache

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SESSION_TYPE"] = "cachelib"
app.config["SESSION_CACHELIB"] = FileSystemCache(".sessions")
app.config["SESSION_PERMANENT"] = False

Session(app)


# Connect to the original database or a specified database.
def get_connection(database=None):
    if database is None:
        database = os.getenv("DB_NAME")

    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=database,
        cursorclass=pymysql.cursors.DictCursor
    )


@app.route("/")
def home():
    return redirect("/register")


@app.route("/register", methods=["GET", "POST"])
def register():
    errors = []

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name:
            errors.append("Name is required")

        if not email:
            errors.append("Email is required")

        if not password:
            errors.append("Password is required")

        if not confirm_password:
            errors.append("Confirm password is required")

        if password and confirm_password and password != confirm_password:
            errors.append("Passwords do not match")

        if len(name) > 100:
            errors.append("Name is too long")

        if len(email) > 255:
            errors.append("Email is too long")

        if len(password.encode("utf-8")) > 72:
            errors.append("Password must be at most 72 bytes")

        if not errors:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")

            connection = None

            try:
                connection = get_connection()

                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO users (email, name, password_hash) "
                        "VALUES (%s, %s, %s)",
                        (email, name, password_hash)
                    )

                    user_id = cursor.lastrowid

                connection.commit()

            except pymysql.IntegrityError as error:
                if error.args[0] == 1062:
                    errors.append("Email Already Exists")
                else:
                    errors.append("Could not create the account")

            except pymysql.MySQLError as error:
                print("MySQL error:", error)
                errors.append("Database unavailable. Please try again")

            finally:
                if connection is not None:
                    connection.close()

            if not errors:
                session.clear()
                session["user_id"] = user_id
                session["name"] = name
                app.session_interface.regenerate(session)

                return redirect("/todos")

    return render_template("register.html", errors=errors)


@app.route("/todos")
def todos():
    if "user_id" not in session:
        return redirect("/register")

    return render_template("todos.html")


# F2.1: Display authors and books using SELECT.
@app.route("/library")
def library():
    if "user_id" not in session:
        return redirect("/register")

    connection = get_connection("library")

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT *\nFROM AUTHOR')
            authors = cursor.fetchall()

            cursor.execute('SELECT *\nFROM BOOK')
            books = cursor.fetchall()

    finally:
        connection.close()

    return render_template(
        "library.html",
        authors=authors,
        books=books
    )


# F2.2: Add an author using INSERT.
@app.route("/add_author", methods=["GET", "POST"])
def add_author():
    if "user_id" not in session:
        return redirect("/register")

    errors = []

    if request.method == "POST":
        author_id_text = request.form.get("author_id", "").strip()
        name = request.form.get("name", "").strip()
        country = request.form.get("country", "").strip()

        try:
            author_id = int(author_id_text)

            if not 1 <= author_id <= 2147483647:
                errors.append("Enter a valid positive author ID.")

        except ValueError:
            errors.append("Author ID must be a whole number.")

        if not name or len(name) > 100:
            errors.append("Enter a name of up to 100 characters.")

        if not country or len(country) > 50:
            errors.append("Enter a country of up to 50 characters.")

        if not errors:
            connection = None

            try:
                connection = get_connection("library")

                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO AUTHOR (author_id, name, country) "
                        "VALUES (%s, %s, %s)",
                        (author_id, name, country)
                    )

                connection.commit()
                return redirect("/library")

            except pymysql.IntegrityError as error:
                if connection is not None:
                    connection.rollback()

                if error.args[0] == 1062:
                    errors.append("This author ID already exists.")
                else:
                    errors.append("Could not add the author.")

            except pymysql.MySQLError as error:
                if connection is not None:
                    connection.rollback()

                print("MySQL error:", error)
                errors.append("Database unavailable. Please try again.")

            finally:
                if connection is not None:
                    connection.close()

    return render_template("add_author.html", errors=errors)


# F2.2: Add a book using INSERT.
@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if "user_id" not in session:
        return redirect("/register")

    errors = []
    authors = []
    publishers = []
    categories = []
    connection = None

    try:
        connection = get_connection("library")

        with connection.cursor() as cursor:
            cursor.execute('SELECT *\nFROM AUTHOR')
            authors = cursor.fetchall()
            cursor.execute('SELECT *\nFROM PUBLISHER')
            publishers = cursor.fetchall()
            cursor.execute('SELECT *\nFROM CATEGORY')
            categories = cursor.fetchall()

        if request.method == "POST":
            book_id_text = request.form.get("book_id", "").strip()
            title = request.form.get("title", "").strip()
            price_text = request.form.get("price", "").strip()
            author_id_text = request.form.get("author_id", "").strip()

            try:
                book_id = int(book_id_text)

                if not 1 <= book_id <= 2147483647:
                    errors.append("Enter a valid positive book ID.")

            except ValueError:
                errors.append("Book ID must be a whole number.")

            if not title or len(title) > 150:
                errors.append("Enter a title of up to 150 characters.")

            try:
                price = Decimal(price_text)

                if not price.is_finite():
                    errors.append("Enter a valid price.")

                elif not 0 <= price <= Decimal("99999999.99"):
                    errors.append(
                        "Price must be between 0 and 99999999.99."
                    )

                elif price != price.quantize(Decimal("0.01")):
                    errors.append("Use at most two decimal places.")

            except InvalidOperation:
                errors.append("Enter a valid price.")

            valid_author_ids = [
                str(author["author_id"]) for author in authors
            ]

            if author_id_text not in valid_author_ids:
                errors.append("Choose an existing author.")

            publisher_id_text = request.form.get("publisher_id", "")
            category_id_text = request.form.get("category_id", "")
            if publisher_id_text not in [str(p["publisher_id"]) for p in publishers]:
                errors.append("Choose an existing publisher.")
            if category_id_text not in [str(c["category_id"]) for c in categories]:
                errors.append("Choose an existing category.")
            year_text = request.form.get("publish_year", "").strip()
            publish_year = None
            if year_text:
                try:
                    publish_year = int(year_text)
                    if not 1 <= publish_year <= 9999:
                        errors.append("Publication year must be from 1 to 9999.")
                except ValueError:
                    errors.append("Enter a whole publication year.")

            if not errors:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO BOOK "
                        "(book_id, title, price, author_id, publisher_id, category_id, publish_year) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (
                            book_id,
                            title,
                            price,
                            int(author_id_text), int(publisher_id_text),
                            int(category_id_text), publish_year
                        )
                    )

                connection.commit()
                return redirect("/library")

    except pymysql.IntegrityError as error:
        if connection is not None:
            connection.rollback()

        if error.args[0] == 1062:
            errors.append("This book ID already exists.")
        elif error.args[0] == 1452:
            errors.append("The selected author no longer exists.")
        else:
            errors.append("Could not add the book.")

    except pymysql.MySQLError as error:
        if connection is not None:
            connection.rollback()

        print("MySQL error:", error)
        errors.append("Database unavailable. Please try again.")

    finally:
        if connection is not None:
            connection.close()

    return render_template(
        "add_book.html",
        errors=errors,
        authors=authors, publishers=publishers, categories=categories
    )


# F2.3: Edit an author using UPDATE.
@app.route("/edit_author/<int:author_id>", methods=["GET", "POST"])
def edit_author(author_id):
    if "user_id" not in session:
        return redirect("/register")

    errors = []
    author = None
    connection = None

    try:
        connection = get_connection("library")

        with connection.cursor() as cursor:
            # Retrieve the selected author by primary key.
            cursor.execute(
                'SELECT *\nFROM AUTHOR\nWHERE author_id = %s',
                (author_id,)
            )
            author = cursor.fetchone()

        if author is None:
            return "Author not found", 404

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            country = request.form.get("country", "").strip()

            if not name or len(name) > 100:
                errors.append("Enter a name of up to 100 characters.")

            if not country or len(country) > 50:
                errors.append("Enter a country of up to 50 characters.")

            # Keep entered values visible if validation fails.
            author["name"] = name
            author["country"] = country

            if not errors:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE AUTHOR "
                        "SET name = %s, country = %s "
                        "WHERE author_id = %s",
                        (name, country, author_id)
                    )

                connection.commit()
                return redirect("/library")

    except pymysql.MySQLError as error:
        if connection is not None:
            connection.rollback()

        print("MySQL error:", error)

        if author is None:
            return "Database unavailable. Please try again.", 503

        errors.append("Could not save the changes. Please try again.")

    finally:
        if connection is not None:
            connection.close()

    return render_template(
        "edit_author.html",
        author=author,
        errors=errors
    )


# F2.3: Edit a book using UPDATE.
@app.route("/edit_book/<int:book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    if "user_id" not in session:
        return redirect("/register")

    errors = []
    book = None
    authors = []
    publishers = []
    categories = []
    connection = None

    try:
        connection = get_connection("library")

        with connection.cursor() as cursor:
            # Retrieve the selected book by primary key.
            cursor.execute(
                'SELECT *\nFROM BOOK\nWHERE book_id = %s',
                (book_id,)
            )
            book = cursor.fetchone()

            # Retrieve authors for the selection list.
            cursor.execute('SELECT *\nFROM AUTHOR')
            authors = cursor.fetchall()
            cursor.execute('SELECT *\nFROM PUBLISHER')
            publishers = cursor.fetchall()
            cursor.execute('SELECT *\nFROM CATEGORY')
            categories = cursor.fetchall()

        if book is None:
            return "Book not found", 404

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            price_text = request.form.get("price", "").strip()
            author_id_text = request.form.get("author_id", "").strip()

            if not title or len(title) > 150:
                errors.append("Enter a title of up to 150 characters.")

            try:
                price = Decimal(price_text)

                if not price.is_finite():
                    errors.append("Enter a valid price.")

                elif not 0 <= price <= Decimal("99999999.99"):
                    errors.append(
                        "Price must be between 0 and 99999999.99."
                    )

                elif price != price.quantize(Decimal("0.01")):
                    errors.append("Use at most two decimal places.")

            except InvalidOperation:
                errors.append("Enter a valid price.")

            valid_author_ids = [
                str(author["author_id"]) for author in authors
            ]

            if author_id_text not in valid_author_ids:
                errors.append("Choose an existing author.")

            publisher_id_text = request.form.get("publisher_id", "")
            category_id_text = request.form.get("category_id", "")
            if publisher_id_text not in [str(p["publisher_id"]) for p in publishers]:
                errors.append("Choose an existing publisher.")
            if category_id_text not in [str(c["category_id"]) for c in categories]:
                errors.append("Choose an existing category.")
            year_text = request.form.get("publish_year", "").strip()
            publish_year = None
            if year_text:
                try:
                    publish_year = int(year_text)
                    if not 1 <= publish_year <= 9999:
                        errors.append("Publication year must be from 1 to 9999.")
                except ValueError:
                    errors.append("Enter a whole publication year.")

            # Keep entered values visible if validation fails.
            book["title"] = title
            book["price"] = price_text
            book["author_id"] = author_id_text

            if not errors:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE BOOK "
                        "SET title = %s, price = %s, author_id = %s, publisher_id = %s, category_id = %s, publish_year = %s "
                        "WHERE book_id = %s",
                        (
                            title,
                            price,
                            int(author_id_text), int(publisher_id_text),
                            int(category_id_text), publish_year, book_id
                        )
                    )

                connection.commit()
                return redirect("/library")

    except pymysql.IntegrityError:
        if connection is not None:
            connection.rollback()

        errors.append("The selected author no longer exists.")

    except pymysql.MySQLError as error:
        if connection is not None:
            connection.rollback()

        print("MySQL error:", error)

        if book is None:
            return "Database unavailable. Please try again.", 503

        errors.append("Could not save the changes. Please try again.")

    finally:
        if connection is not None:
            connection.close()

    return render_template(
        "edit_book.html",
        book=book,
        authors=authors, publishers=publishers, categories=categories,
        errors=errors
    )



# Lab 4: run SELECT queries and close the connection after reading the rows.
def read_rows(sql, values=()):
    connection = get_connection("library")
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, values)
            return cursor.fetchall()
    finally:
        connection.close()

@app.route("/delete_author/<int:author_id>", methods=["POST"])
def delete_author(author_id):
    return delete_row("AUTHOR", "author_id", author_id)

@app.route("/delete_book/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    return delete_row("BOOK", "book_id", book_id)

def delete_row(table, column, row_id):
    if "user_id" not in session:
        return redirect("/register")
    connection = get_connection("library")
    try:
        with connection.cursor() as cursor:
            # Table and column names come only from the two routes above.
            cursor.execute("DELETE FROM " + table + " WHERE " + column + " = %s", (row_id,))
        connection.commit()
    finally:
        connection.close()
    return redirect("/library")

@app.route("/library/search")
def search_books():
    if "user_id" not in session:
        return redirect("/register")
    errors = []
    books = []
    categories = read_rows('SELECT *\nFROM CATEGORY\nORDER BY name')
    keyword = request.args.get("keyword", "").strip()
    try:
        minimum = Decimal(request.args.get("min_price", "").strip() or "0")
        maximum = Decimal(request.args.get("max_price", "").strip() or "99999999.99")
        if not minimum.is_finite() or not maximum.is_finite():
            raise ValueError()
        if not 0 <= minimum <= maximum <= Decimal("99999999.99"):
            raise ValueError()
        category_id = int(request.args.get("category_id", "0"))
        if category_id != 0 and category_id not in [c["category_id"] for c in categories]:
            raise ValueError()
    except (ValueError, InvalidOperation):
        errors.append("Enter a valid price range and category (minimum must not exceed maximum).")
    if not errors:
        books = read_rows(SEARCH_SQL, ("%" + keyword + "%", minimum, maximum, category_id, category_id))
    return render_template("search_books.html", categories=categories, books=books, errors=errors)

SEARCH_SQL = 'SELECT B.book_id, B.title, B.price, C.name AS category\nFROM BOOK AS B\nJOIN CATEGORY AS C ON B.category_id = C.category_id\nWHERE B.title LIKE %s AND B.price BETWEEN %s AND %s\n AND (%s = 0 OR B.category_id = %s)\nORDER BY B.price, B.book_id'

@app.route("/library/catalogue")
def catalogue():
    if "user_id" not in session:
        return redirect("/register")
    sections = []
    sections.append(('All books', read_rows('SELECT B.book_id, B.title, B.price, B.publish_year, A.name AS author, P.name AS publisher, C.name AS category\nFROM BOOK AS B\nJOIN AUTHOR AS A ON B.author_id = A.author_id\nJOIN PUBLISHER AS P ON B.publisher_id = P.publisher_id\nJOIN CATEGORY AS C ON B.category_id = C.category_id\nORDER BY B.book_id')))
    return render_template("lab4_results.html", title='Catalogue', sections=sections)

@app.route("/library/reports")
def reports():
    if "user_id" not in session:
        return redirect("/register")
    sections = []
    sections.append(('Books and average price per category', read_rows('SELECT C.name AS category, COUNT(B.book_id) AS books, AVG(B.price) AS average_price\nFROM CATEGORY AS C\nLEFT OUTER JOIN BOOK AS B ON C.category_id = B.category_id\nGROUP BY C.category_id, C.name\nORDER BY C.category_id')))
    sections.append(('Authors with at least two books', read_rows('SELECT A.name AS author, COUNT(B.book_id) AS books\nFROM AUTHOR AS A\nJOIN BOOK AS B ON A.author_id = B.author_id\nGROUP BY A.author_id, A.name\nHAVING COUNT(B.book_id) >= 2\nORDER BY A.author_id')))
    sections.append(('Library prices', read_rows('SELECT SUM(price) AS total_price, MIN(price) AS smallest_price, MAX(price) AS largest_price FROM BOOK')))
    return render_template("lab4_results.html", title='Reports', sections=sections)

@app.route("/library/loans")
def loans():
    if "user_id" not in session:
        return redirect("/register")
    sections = []
    sections.append(('Loans not returned yet', read_rows('SELECT L.loan_id, B.title, M.name AS member, L.loan_date\nFROM LOAN AS L\nJOIN BOOK AS B ON L.book_id = B.book_id\nJOIN MEMBER AS M ON L.member_id = M.member_id\nWHERE L.return_date IS NULL\nORDER BY L.loan_id')))
    sections.append(('Members who never borrowed', read_rows('SELECT M.member_id, M.name, M.email\nFROM MEMBER AS M\nLEFT OUTER JOIN LOAN AS L ON M.member_id = L.member_id\nWHERE L.loan_id IS NULL\nORDER BY M.member_id')))
    sections.append(('Books never borrowed', read_rows('SELECT B.book_id, B.title\nFROM BOOK AS B\nLEFT OUTER JOIN LOAN AS L ON B.book_id = L.book_id\nWHERE L.loan_id IS NULL\nORDER BY B.book_id')))
    return render_template("lab4_results.html", title='Loans', sections=sections)

@app.route("/library/most_borrowed")
def most_borrowed():
    if "user_id" not in session:
        return redirect("/register")
    sections = []
    sections.append(('Top three books', read_rows('SELECT B.book_id, B.title, COUNT(L.loan_id) AS loans\nFROM BOOK AS B\nJOIN LOAN AS L ON B.book_id = L.book_id\nGROUP BY B.book_id, B.title\nORDER BY loans DESC, B.book_id\nLIMIT 3')))
    sections.append(('Top member', read_rows('SELECT M.member_id, M.name, COUNT(L.loan_id) AS loans\nFROM MEMBER AS M\nJOIN LOAN AS L ON M.member_id = L.member_id\nGROUP BY M.member_id, M.name\nORDER BY loans DESC, M.member_id\nLIMIT 1')))
    return render_template("lab4_results.html", title='Most borrowed', sections=sections)

@app.route("/library/authors_books")
def authors_books():
    if "user_id" not in session:
        return redirect("/register")
    sections = []
    sections.append(('Every author and book count', read_rows('SELECT A.author_id, A.name, COUNT(B.book_id) AS books\nFROM AUTHOR AS A\nLEFT OUTER JOIN BOOK AS B ON A.author_id = B.author_id\nGROUP BY A.author_id, A.name\nORDER BY A.author_id')))
    sections.append(('Author and publisher from the same country', read_rows('SELECT B.title, A.name AS author, P.name AS publisher, A.country\nFROM BOOK AS B\nJOIN AUTHOR AS A ON B.author_id = A.author_id\nJOIN PUBLISHER AS P ON B.publisher_id = P.publisher_id\nWHERE A.country = P.country\nORDER BY B.book_id')))
    return render_template("lab4_results.html", title='Authors and books', sections=sections)

if __name__ == "__main__":
    app.run()
