# Lab 4 - Library Website

Name: Mohamed Nader El-ashry
Student ID: 2304082

## Requirements

- Python
- MySQL Server and MySQL Workbench

## How to run

1. In MySQL Workbench, run these files in order:
   - problem2_DDL.sql
   - problem2_DML.sql
   - problem2_Queries.sql

   DDL resets the library database. Run DML only once after DDL.

2. If the registration database does not exist, run:
   website/database/schema.sql

   This script resets registration, so skip it if you already have it.

3. Open a terminal inside the website folder and run:

```bat
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

4. Edit .env with your MySQL password and a long random SECRET_KEY.
   Keep these settings:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_NAME=registration
```

5. Start the website:

```bat
.\.venv\Scripts\python.exe app.py
```

6. Open http://127.0.0.1:5000/register and create an account.
   Then open http://127.0.0.1:5000/library.
   Keep the terminal running while using the website.

## Features

- Search books using SQL placeholders.
- Show the book catalogue.
- Show reports and loans.
- Show the most borrowed books and member.
- Show author book counts and matching author/publisher countries.
- Add, edit and delete books and authors.

## Files

- problem2_DDL.sql
- problem2_DML.sql
- problem2_Queries.sql
- website/
- README.md

Do not upload .env, .venv, .sessions or __pycache__ to GitHub.
Keep .env.example and requirements.txt.